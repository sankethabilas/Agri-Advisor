"""
Agri-Advisor NLP Layer (Task T-10).
Provides Intent Classification and Named Entity Recognition (NER) for agricultural queries.
Supports Sri Lankan agricultural contexts, local crops, symptom patterns, and locations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

logger = logging.getLogger("agri_advisor.nlp")

# Lazy spaCy loading to avoid slow module imports when not required immediately
_spacy_nlp = None

def get_spacy_nlp():
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            import spacy
            _spacy_nlp = spacy.load("en_core_web_sm")
        except Exception as error:
            logger.warning(
                "Could not load spaCy en_core_web_sm (%s). Falling back to regex-only tokenization.",
                type(error).__name__,
            )
            _spacy_nlp = False
    return _spacy_nlp if _spacy_nlp is not False else None


# ============================================================================
# T-10.4: Agricultural Vocabulary Lists for Sri Lankan Context
# ============================================================================

# Crop canonical map: variant -> canonical name
CROP_VOCABULARY: Dict[str, str] = {
    # Paddy / Rice
    "rice": "Paddy",
    "paddy": "Paddy",
    "wee": "Paddy",
    "nel": "Paddy",
    "bg352": "Paddy",
    "bg358": "Paddy",
    "bw367": "Paddy",
    "ld365": "Paddy",
    "at362": "Paddy",
    # Tomato
    "tomato": "Tomato",
    "tomatoes": "Tomato",
    "thakkali": "Tomato",
    # Chilli
    "chilli": "Chilli",
    "chili": "Chilli",
    "chillies": "Chilli",
    "chilies": "Chilli",
    "miris": "Chilli",
    "hot pepper": "Chilli",
    "capsicum": "Chilli",
    # Maize / Corn
    "maize": "Maize",
    "corn": "Maize",
    "badairingu": "Maize",
    # Brinjal / Eggplant
    "brinjal": "Brinjal",
    "eggplant": "Brinjal",
    "aubergine": "Brinjal",
    "wambatu": "Brinjal",
    # Onion
    "onion": "Onion",
    "onions": "Onion",
    "big onion": "Onion",
    "red onion": "Onion",
    "lunu": "Onion",
    # Potato
    "potato": "Potato",
    "potatoes": "Potato",
    "ala": "Potato",
    # Legumes & Pulses
    "mung bean": "Mung Bean",
    "mungbean": "Mung Bean",
    "green gram": "Mung Bean",
    "mun": "Mung Bean",
    "cowpea": "Cowpea",
    "soybean": "Soybean",
    "soya": "Soybean",
    # Commercial & Plantation Crops
    "tea": "Tea",
    "rubber": "Rubber",
    "coconut": "Coconut",
    "pol": "Coconut",
    "sugarcane": "Sugarcane",
    "cinnamon": "Cinnamon",
    "pepper": "Black Pepper",
    "black pepper": "Black Pepper",
    # Fruits
    "banana": "Banana",
    "kesel": "Banana",
    "mango": "Mango",
    "amba": "Mango",
    "papaya": "Papaya",
    "pineapple": "Pineapple",
    # Vegetables
    "cabbage": "Cabbage",
    "carrot": "Carrot",
    "beans": "Beans",
    "leeks": "Leeks",
    "cucumber": "Cucumber",
    "pumpkin": "Pumpkin",
    "bitter gourd": "Bitter Gourd",
    "karawila": "Bitter Gourd",
    "snake gourd": "Snake Gourd",
    "pathola": "Snake Gourd",
    "okra": "Okra",
    "ladies finger": "Okra",
    "bandakka": "Okra",
}

# Sri Lanka 25 Districts (normalized lower -> Canonical Title)
DISTRICTS: Dict[str, str] = {
    "ampara": "Ampara",
    "anuradhapura": "Anuradhapura",
    "badulla": "Badulla",
    "batticaloa": "Batticaloa",
    "colombo": "Colombo",
    "galle": "Galle",
    "gampaha": "Gampaha",
    "hambantota": "Hambantota",
    "jaffna": "Jaffna",
    "kalutara": "Kalutara",
    "kandy": "Kandy",
    "kegalle": "Kegalle",
    "kilinochchi": "Kilinochchi",
    "kurunegala": "Kurunegala",
    "mannar": "Mannar",
    "matale": "Matale",
    "matara": "Matara",
    "monaragala": "Monaragala",
    "moneragala": "Monaragala",
    "mullaitivu": "Mullaitivu",
    "nuwara eliya": "Nuwara Eliya",
    "polonnaruwa": "Polonnaruwa",
    "puttalam": "Puttalam",
    "ratnapura": "Ratnapura",
    "trincomalee": "Trincomalee",
    "vavuniya": "Vavuniya",
}

# Sri Lankan Agro-Ecological Zones & Regions
REGIONS_AND_ZONES: Dict[str, str] = {
    "dry zone": "Dry Zone",
    "wet zone": "Wet Zone",
    "intermediate zone": "Intermediate Zone",
    "upcountry": "Upcountry",
    "lowcountry": "Lowcountry",
    "midcountry": "Midcountry",
    "dryzone": "Dry Zone",
    "wetzone": "Wet Zone",
    "mahaweli": "Mahaweli",
}

# Cultivation Seasons
SEASONS: Dict[str, str] = {
    "maha": "Maha",
    "yala": "Yala",
    "inter-monsoon": "Inter-monsoon",
    "mid season": "Mid-season",
}

# Symptom & Disease Indicator Phrases
SYMPTOM_PHRASES: List[str] = [
    "yellow spots", "yellow spot", "yellowing leaves", "yellow leaves", "yellowing", "yellow leaf",
    "brown spots", "brown spot", "brown lesions", "brown patches", "brown patch", "brown discoloration",
    "leaf blast", "neck blast", "collar rot", "root rot", "stem rot", "foot rot", "fruit rot",
    "bacterial blight", "early blight", "late blight", "sheath blight", "sheath rot",
    "powdery mildew", "downy mildew", "sooty mould", "leaf curl", "curling leaves", "curled leaves",
    "wilting", "wilt", "wilted", "drooping", "damping off", "dieback", "die back",
    "leaf spots", "black spots", "white spots", "cankers", "galls", "scab", "rust",
    "stem borer", "brown planthopper", "bph", "gall midge", "caterpillar", "armyworm",
    "aphids", "whiteflies", "whitefly", "thrips", "mites", "mealybug", "mealybugs",
    "leaf miner", "pod borer", "fruit fly", "cutworm", "hopper burn", "hopperburn",
    "stunted growth", "pale leaves", "burnt leaves", "lesions on leaves", "leaf drying",
    "drying of tips", "tip burn", "chlorosis", "necrosis", "holes in leaves", "skeletonized leaves"
]

# Keywords for Intent Scoring
DISEASE_KEYWORDS = {
    "spot", "spots", "yellow", "yellowing", "brown", "black", "blast", "rot", "rotting", "wilt",
    "wilting", "lesion", "lesions", "fungus", "fungal", "bacteria", "bacterial", "virus", "viral",
    "pest", "pests", "caterpillar", "bug", "bugs", "insect", "insects", "worm", "worms", "disease",
    "diseases", "symptom", "symptoms", "dying", "blight", "curl", "curling", "curled", "mildew",
    "canker", "scab", "rust", "infestation", "infected", "damage", "damaged", "eaten", "holes",
    "borer", "hopper", "whitefly", "aphid", "thrips", "mite", "mites", "drying", "chlorosis",
    "fungicide", "pesticide", "insecticide", "treatment", "cure", "smell", "rotted", "foul"
}

WEATHER_KEYWORDS = {
    "weather", "rain", "raining", "rainy", "rainfall", "forecast", "monsoon", "temperature",
    "temp", "humidity", "flood", "flooding", "drought", "wind", "windy", "storm", "cyclone",
    "sunshine", "sunny", "precipitation", "climate", "heat", "hot", "cold", "dew", "fog",
    "cloudy", "showers", "dry", "spell", "dry spell", "wet"
}

CROP_ADVICE_KEYWORDS = {
    "variety", "varieties", "fertilizer", "fertilizers", "fertiliser", "fertilisers", "urea",
    "tsp", "mop", "npk", "planting", "plant", "sowing", "sow", "spacing", "harvest", "harvesting",
    "yield", "cultivation", "cultivate", "maha", "yala", "preparation", "nursery", "transplanting",
    "irrigation", "water", "seed", "seeds", "dosage", "weed", "weeds", "pruning", "stage",
    "maturity", "storage", "store", "rotation", "distance", "rate", "guide", "spacing"
}

GENERAL_POLICY_KEYWORDS = {
    "insurance", "scheme", "schemes", "subsidy", "subsidies", "hotline", "contact", "officer",
    "service center", "agrarian", "extension", "institute", "training", "program", "programs",
    "buy", "purchase", "how does", "thank you", "thanks", "hello", "good morning", "good afternoon"
}

IntentType = Literal["disease_diagnosis", "weather_query", "crop_advice", "mixed_query", "general_query"]


@dataclass
class ExtractedEntities:
    crop: Optional[str] = None
    symptoms: List[str] = field(default_factory=list)
    location: Optional[str] = None
    district: Optional[str] = None
    region: Optional[str] = None
    season: Optional[str] = None
    stage: Optional[str] = None
    raw_entities: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crop": self.crop,
            "symptoms": self.symptoms,
            "location": self.location,
            "district": self.district,
            "region": self.region,
            "season": self.season,
            "stage": self.stage,
            "raw_entities": self.raw_entities,
        }


@dataclass
class NLPResult:
    intent: IntentType
    confidence: float
    entities: ExtractedEntities
    intent_scores: Dict[str, float]
    normalized_query: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "confidence": round(self.confidence, 4),
            "entities": self.entities.to_dict(),
            "intent_scores": {k: round(v, 4) for k, v in self.intent_scores.items()},
            "normalized_query": self.normalized_query,
        }


# ============================================================================
# T-10.3: Named Entity Recognition (NER)
# ============================================================================

class EntityExtractor:
    """Extracts crops, symptoms, locations, seasons, and cultivation stages."""

    def __init__(self) -> None:
        self.spacy_nlp = get_spacy_nlp()
        self._compile_symptom_regexes()

    def _compile_symptom_regexes(self) -> None:
        """Compile regex patterns for multi-word and single-word symptoms."""
        # Sort by longest string first so 'yellow spots on the leaves' or 'yellow spots' matches before 'yellow'
        sorted_symptoms = sorted(SYMPTOM_PHRASES, key=len, reverse=True)
        self.symptom_patterns = [
            (symptom, re.compile(rf"\b{re.escape(symptom)}\b", re.IGNORECASE))
            for symptom in sorted_symptoms
        ]

    def extract_crop(self, text: str) -> Optional[str]:
        """Extract agricultural crop name and normalize to standard English title."""
        text_lower = text.lower()
        # Sort crop keys by length descending to match 'mung bean' before 'bean'
        sorted_crop_keys = sorted(CROP_VOCABULARY.keys(), key=len, reverse=True)
        for crop_key in sorted_crop_keys:
            pattern = rf"\b{re.escape(crop_key)}\b"
            if re.search(pattern, text_lower):
                return CROP_VOCABULARY[crop_key]
        return None

    def extract_symptoms(self, text: str) -> List[str]:
        """Extract all matched agricultural symptoms from the query."""
        found_symptoms: List[str] = []
        text_lower = text.lower()

        # 1. Match against predefined curated symptom phrases
        for symptom_str, pattern in self.symptom_patterns:
            if pattern.search(text_lower):
                # Avoid adding substring duplicates (e.g. don't add 'yellow spot' if 'yellow spots' already added)
                if not any(symptom_str in existing for existing in found_symptoms):
                    found_symptoms.append(symptom_str)

        # 2. Extract composite descriptive patterns like 'X spots on the Y'
        composite_patterns = [
            r"\b(yellow|brown|black|white|dark)\s+(spots?|lesions?|patches?|specks?)\s+(on\s+(the\s+)?(leaves|leaf|stem|stalk|panicle|fruit|grain))\b",
            r"\b(curling|drying|yellowing|wilting|drooping|browning)\s+(of\s+(the\s+)?(leaves|leaf|tips|roots|seedlings))\b",
            r"\b(holes|eaten\s+parts)\s+(in\s+(the\s+)?(leaves|fruits|stems))\b",
        ]
        for cpat in composite_patterns:
            matches = re.finditer(cpat, text_lower)
            for m in matches:
                matched_phrase = m.group(0)
                if not any(matched_phrase in existing for existing in found_symptoms):
                    found_symptoms.append(matched_phrase)

        # 3. If still empty, check for general single disease keywords
        if not found_symptoms:
            single_words = ["blast", "blight", "rot", "wilt", "caterpillar", "borer", "rust", "mildew", "dieback"]
            for word in single_words:
                if re.search(rf"\b{word}\b", text_lower):
                    found_symptoms.append(word)

        return found_symptoms

    def extract_location(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract location entity (district, general location, agro-ecological zone)."""
        text_lower = text.lower()
        district: Optional[str] = None
        region: Optional[str] = None
        location: Optional[str] = None

        # 1. Check districts
        for d_key, d_name in DISTRICTS.items():
            pattern = rf"\b{re.escape(d_key)}\b"
            if re.search(pattern, text_lower):
                district = d_name
                location = d_name
                break

        # 2. Check agro-ecological zones
        for r_key, r_name in REGIONS_AND_ZONES.items():
            pattern = rf"\b{re.escape(r_key)}\b"
            if re.search(pattern, text_lower):
                region = r_name
                if not location:
                    location = r_name
                break

        # 3. spaCy GPE fallback if available
        if not location and self.spacy_nlp:
            try:
                doc = self.spacy_nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ("GPE", "LOC"):
                        location = ent.text.strip().title()
                        # Check if matches any district
                        if location.lower() in DISTRICTS:
                            district = DISTRICTS[location.lower()]
                        break
            except Exception:
                pass

        return location, district, region

    def extract_season(self, text: str) -> Optional[str]:
        """Extract cultivation season (Maha / Yala)."""
        text_lower = text.lower()
        for s_key, s_name in SEASONS.items():
            if re.search(rf"\b{re.escape(s_key)}\b", text_lower):
                return s_name
        return None

    def extract_growth_stage(self, text: str) -> Optional[str]:
        """Extract crop growth stage."""
        stages = {
            "nursery": "Nursery",
            "seedling": "Seedling",
            "vegetative": "Vegetative",
            "tillering": "Tillering",
            "panicle initiation": "Panicle Initiation",
            "flowering": "Flowering",
            "grain filling": "Grain Filling",
            "heading": "Heading",
            "milking": "Milking",
            "dough stage": "Dough Stage",
            "ripening": "Ripening",
            "maturity": "Maturity",
            "harvest": "Harvest",
            "harvesting": "Harvest",
            "post-harvest": "Post-Harvest",
        }
        text_lower = text.lower()
        for stage_key, stage_val in stages.items():
            if re.search(rf"\b{re.escape(stage_key)}\b", text_lower):
                return stage_val
        return None

    def extract_all(self, text: str) -> ExtractedEntities:
        """Run complete Named Entity Recognition extraction."""
        crop = self.extract_crop(text)
        symptoms = self.extract_symptoms(text)
        location, district, region = self.extract_location(text)
        season = self.extract_season(text)
        stage = self.extract_growth_stage(text)

        raw_entities: Dict[str, Any] = {}
        if self.spacy_nlp:
            try:
                doc = self.spacy_nlp(text)
                for ent in doc.ents:
                    raw_entities[ent.label_] = ent.text
            except Exception:
                pass

        return ExtractedEntities(
            crop=crop,
            symptoms=symptoms,
            location=location,
            district=district,
            region=region,
            season=season,
            stage=stage,
            raw_entities=raw_entities,
        )


# ============================================================================
# T-10.1: Intent Classifier
# ============================================================================

class IntentClassifier:
    """Classifies user queries into agricultural intent categories."""

    def __init__(self) -> None:
        self.entity_extractor = EntityExtractor()

    def classify(self, text: str, entities: Optional[ExtractedEntities] = None) -> Tuple[IntentType, float, Dict[str, float]]:
        """
        Classifies query into one of:
        - disease_diagnosis
        - weather_query
        - crop_advice
        - mixed_query
        - general_query
        """
        if not text or not text.strip():
            return "general_query", 0.50, {"general_query": 1.0}

        if entities is None:
            entities = self.entity_extractor.extract_all(text)

        tokens = set(re.findall(r"\b[a-z0-9_-]+\b", text.lower()))
        text_lower = text.lower()

        # Score components
        disease_score = 0.0
        weather_score = 0.0
        crop_score = 0.0

        # 0. Check general policy, contact, or greeting phrases first
        general_policy_matches = tokens.intersection(GENERAL_POLICY_KEYWORDS)
        if general_policy_matches and not entities.symptoms:
            # If query is specifically about insurance, subsidies, contacts, or greetings
            if any(w in text_lower for w in ["insurance", "subsidy", "subsidies", "contact", "officer", "hotline", "training", "how does", "thank you", "thanks", "hello", "good morning", "service center", "buy certified seeds", "where can i buy"]):
                return "general_query", 0.90, {"general_query": 1.0, "disease_diagnosis": 0.0, "weather_query": 0.0, "crop_advice": 0.0}

        # 1. Match keywords
        disease_token_matches = tokens.intersection(DISEASE_KEYWORDS)
        weather_token_matches = tokens.intersection(WEATHER_KEYWORDS)
        crop_token_matches = tokens.intersection(CROP_ADVICE_KEYWORDS)

        # Keyword weights (0.35 per unique keyword to allow single strong keyword trigger)
        disease_score += len(disease_token_matches) * 0.35
        weather_score += len(weather_token_matches) * 0.35
        crop_score += len(crop_token_matches) * 0.35

        # 2. Symptoms presence heavily boosts disease intent
        if entities.symptoms:
            disease_score += 0.60 + (0.15 * len(entities.symptoms))

        # 3. Weather phrase patterns
        weather_phrases = [
            "will it rain", "is it going to rain", "weather forecast", "temperature in",
            "heavy rain", "rain forecast", "flood risk", "drought conditions", "humidity level",
            "chances of rain", "climate in", "expected rainfall", "dry spell", "rain prediction",
            "monsoon rain", "wind speed", "showers in", "weather condition", "cloud cover",
            "weather outlook", "hot weather", "drought and hot"
        ]
        for wp in weather_phrases:
            if wp in text_lower:
                weather_score += 0.55

        # 4. Crop advice phrase patterns
        crop_advice_phrases = [
            "fertilizer schedule", "fertilizer plan", "fertiliser application", "how to grow",
            "how to cultivate", "best variety", "recommended varieties", "seed rate",
            "planting distance", "when to plant", "when to harvest", "spacing between",
            "land preparation", "nursery management", "how much urea", "mop fertilizer",
            "tsp fertilizer", "irrigation schedule", "water management", "best time for planting",
            "harvest and store", "how to harvest", "apply basal fertilizer", "weed control",
            "soil preparation", "transplanting spacing", "spacing recommendation", "high yield"
        ]
        for cp in crop_advice_phrases:
            if cp in text_lower:
                crop_score += 0.55

        # 5. Question structure signals
        if any(w in text_lower for w in ["what disease", "which disease", "identify disease", "cure for", "how to treat", "fungus spreading", "infestation damaging"]):
            disease_score += 0.40

        if any(w in text_lower for w in ["rain", "sunny", "forecast", "monsoon", "temperature"]):
            if entities.district or entities.location:
                weather_score += 0.35

        scores = {
            "disease_diagnosis": disease_score,
            "weather_query": weather_score,
            "crop_advice": crop_score,
        }

        # Multi-intent / Mixed query detection
        # e.g. Weather + Disease (rain worsening blast) or Weather + Crop (rain affecting harvest/fertilizer)
        # Note: Do not treat 'dry zone' / 'wet zone' as pure weather cues if they are agro-ecological regions
        weather_text = text_lower.replace("dry zone", "").replace("wet zone", "").replace("intermediate zone", "")
        has_weather_signal = (weather_score >= 0.50) or any(w in weather_text for w in ["rain", "rainfall", "monsoon", "forecast", "humidity", "hot weather", "drought"])
        has_disease_signal = (disease_score >= 0.35) or bool(entities.symptoms) or any(w in text_lower for w in ["blast", "blight", "fungal", "spots", "fungicide"])
        has_crop_signal = (crop_score >= 0.35) or any(w in text_lower for w in ["harvest", "fertilizer", "fertiliser", "planting", "urea", "tillering"])

        if has_weather_signal and (has_disease_signal or has_crop_signal):
            # Verify it's genuinely a mixed/conditional question
            mixed_cues = ["worsen", "affect", "should i apply", "can i harvest", "before the", "given tomorrow", "during rainy", "rain forecast and", "will high humidity"]
            if any(cue in text_lower for cue in mixed_cues) or (weather_score >= 0.40 and (disease_score >= 0.40 or crop_score >= 0.40)):
                confidence = 0.94
                scores["mixed_query"] = (weather_score + max(disease_score, crop_score)) / 2
                return "mixed_query", confidence, scores

        # Normalize presence threshold (positive intent signal)
        active_intents = [intent for intent, score in scores.items() if score >= 0.30]

        if active_intents:
            best_intent = max(scores, key=scores.get)
            best_score = scores[best_intent]
            # Convert raw score to confidence [0.70 - 0.99]
            confidence = min(0.70 + (best_score * 0.10), 0.99)
            return best_intent, confidence, scores

        # Fallback to general query
        return "general_query", 0.70, scores


# ============================================================================
# T-10.5 & T-10.6: Core Analyzer & General Fallback Handler
# ============================================================================

class NLPAnalyzer:
    """Unified NLP pipeline for Agri-Advisor."""

    def __init__(self) -> None:
        self.entity_extractor = EntityExtractor()
        self.intent_classifier = IntentClassifier()

    def analyze_query(self, query: str) -> NLPResult:
        """
        Execute full intent classification and entity recognition on a farmer query.
        (Subtask T-10.5)
        """
        normalized_query = " ".join(query.strip().split())
        entities = self.entity_extractor.extract_all(normalized_query)
        intent, confidence, scores = self.intent_classifier.classify(normalized_query, entities=entities)

        return NLPResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            intent_scores=scores,
            normalized_query=normalized_query,
        )

    def handle_general_query(self, query: str, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Handle the unrecognised-intent or broad general query path.
        (Subtask T-10.6)
        """
        crop_mention = nlp_result.entities.crop or "your crops"
        location_mention = nlp_result.entities.location or "your area"

        general_guidance = (
            f"Thank you for contacting Agri-Advisor. Your query regarding {crop_mention} in {location_mention} "
            f"has been received. For specific cultivation schedules, disease diagnosis, or weather forecasts, "
            f"please describe the exact symptoms or crop details (e.g., 'My rice has yellow spots on the leaves', "
            f"'Rain forecast for Anuradhapura', or 'Fertilizer guide for maize in Maha season'). "
            f"You can also contact the Department of Agriculture shortcode 1920 for immediate field extension support."
        )

        return {
            "intent": "general_query",
            "answer": general_guidance,
            "entities": nlp_result.entities.to_dict(),
            "suggested_topics": [
                "Crop Disease Identification & Management",
                "7-Day Weather & Rainfall Forecasts",
                "Fertilizer & Cultivation Stage Plans (Maha/Yala)",
                "Pest Risk Warnings & Prevention Measures"
            ],
            "helpline": "1920 (Department of Agriculture Toll-Free)"
        }


# Global singleton instance
nlp_analyzer = NLPAnalyzer()


def analyze_query(query: str) -> NLPResult:
    """Convenience functional wrapper for analyze_query."""
    return nlp_analyzer.analyze_query(query)


def handle_general_query(query: str, nlp_result: Optional[NLPResult] = None) -> Dict[str, Any]:
    """Convenience functional wrapper for handle_general_query."""
    if nlp_result is None:
        nlp_result = nlp_analyzer.analyze_query(query)
    return nlp_analyzer.handle_general_query(query, nlp_result)
