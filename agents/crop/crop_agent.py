from typing import Any, Dict, List, Optional

from knowledge_base.data_loader import (
    get_crop,
    get_crop_varieties,
    get_varieties_by_region,
    get_best_practices,
    get_planting_window,
)


class CropAdvisoryAgent:
    """
    Structured crop advisory agent.

    Uses crop_db.json, best_practices.json and
    seasonal_calendar.json through the T-15 data loaders.
    """

    def __init__(self):
        pass

    # T-19.2
    # Variety recommendation

    def suggest_varieties(
        self,
        crop: str,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest crop varieties.

        Region-specific varieties are preferred.
        Nationally applicable Sri Lanka varieties are used
        as fallback/general recommendations.
        """

        crop_key = crop.strip().lower()

        if location:
            regional_varieties = get_varieties_by_region(
                crop_key,
                location
            )

            if regional_varieties:
                return regional_varieties

        return get_crop_varieties(crop_key)

    # T-19.3
    # Planting advice

    def get_planting_advice(
        self,
        crop: str,
        season: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return planting time, spacing and seed-rate guidance.
        """

        crop_key = crop.strip().lower()

        practices = get_best_practices(crop_key)

        if not practices:
            return {
                "planting_window": [],
                "guidance": []
            }

        planting_guidance = practices.get(
            "planting",
            []
        )

        planting_window = []

        if season:
            planting_window = get_planting_window(
                crop_key,
                season
            )

        return {
            "season": season,
            "planting_window": planting_window,
            "guidance": planting_guidance
        }

    # T-19.4
    # Fertilizer schedule

    def get_fertilizer_schedule(
        self,
        crop: str
    ) -> List[str]:
        """
        Return fertilizer recommendations for the crop.
        """

        practices = get_best_practices(
            crop.strip().lower()
        )

        if not practices:
            return []

        return practices.get(
            "fertilizer",
            []
        )

    # T-19.5
    # Irrigation guidance

    def get_irrigation_guidance(
        self,
        crop: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return irrigation guidance.

        Location is retained in the response so a future
        weather/location layer can refine the advice.
        """

        practices = get_best_practices(
            crop.strip().lower()
        )

        if not practices:
            guidance = []
        else:
            guidance = practices.get(
                "irrigation",
                []
            )

        return {
            "location": location,
            "guidance": guidance
        }

    # T-19.6
    # Pest and disease management

    def get_pest_management(
        self,
        crop: str
    ) -> List[str]:
        """
        Return crop pest and disease management practices.
        """

        practices = get_best_practices(
            crop.strip().lower()
        )

        if not practices:
            return []

        return practices.get(
            "pest_disease_management",
            []
        )

    # T-19.7
    # Harvesting advice

    def get_harvesting_advice(
        self,
        crop: str
    ) -> Dict[str, Any]:
        """
        Return harvesting guidance and expected yield
        where the knowledge base provides it.
        """

        crop_key = crop.strip().lower()

        practices = get_best_practices(crop_key)

        if not practices:
            return {
                "guidance": [],
                "expected_yield": None
            }

        guidance = practices.get(
            "harvesting",
            []
        )

        expected_yield = None

        worked_example = practices.get(
            "worked_example"
        )

        if worked_example:
            expected_yield = worked_example.get(
                "expected_yield"
            )

        return {
            "guidance": guidance,
            "expected_yield": expected_yield
        }

    # T-19.8
    # Rotation

    def get_rotation_recommendations(
        self,
        crop: str
    ) -> List[str]:
        """
        Return crop rotation recommendations.
        """

        practices = get_best_practices(
            crop.strip().lower()
        )

        if not practices:
            return []

        return practices.get(
            "rotation",
            []
        )

    # T-19.8
    # Sustainability

    def get_sustainable_practices(
        self,
        crop: str
    ) -> List[str]:
        """
        Return sustainability recommendations.
        """

        practices = get_best_practices(
            crop.strip().lower()
        )

        if not practices:
            return []

        return practices.get(
            "sustainability",
            []
        )

    # T-19.9
    # Full advisory

    def get_advisory(
        self,
        crop: str,
        location: Optional[str] = None,
        season: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compose the eight advisory sections into one
        structured crop advisory response.
        """

        crop_key = crop.strip().lower()

        crop_record = get_crop(crop_key)

        if not crop_record:
            return {
                "success": False,
                "crop": crop,
                "location": location,
                "season": season,
                "message": (
                    f"No structured crop advisory data "
                    f"available for '{crop}'."
                ),
                "advisory": None
            }

        varieties = self.suggest_varieties(
            crop_key,
            location
        )

        planting = self.get_planting_advice(
            crop_key,
            season
        )

        fertilizer = self.get_fertilizer_schedule(
            crop_key
        )

        irrigation = self.get_irrigation_guidance(
            crop_key,
            location
        )

        pest_management = self.get_pest_management(
            crop_key
        )

        harvesting = self.get_harvesting_advice(
            crop_key
        )

        rotation = self.get_rotation_recommendations(
            crop_key
        )

        sustainability = self.get_sustainable_practices(
            crop_key
        )

        return {
            "success": True,
            "crop": crop_record.get(
                "crop",
                crop
            ),
            "location": location,
            "season": season,

            "advisory": {
                "varieties": varieties,
                "planting": planting,
                "fertilizer": fertilizer,
                "irrigation": irrigation,
                "pest_management": pest_management,
                "harvesting": harvesting,
                "rotation": rotation,
                "sustainability": sustainability
            }
        }


# Simple manual test

if __name__ == "__main__":

    agent = CropAdvisoryAgent()

    result = agent.get_advisory(
        crop="maize",
        location="Sri Lanka",
        season="maha"
    )

    from pprint import pprint

    pprint(result)