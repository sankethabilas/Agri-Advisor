import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DOCUMENTS_PATH = (
    PROJECT_ROOT / "knowledge_base" / "documents.json"
)


STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "and",
    "or",
    "my",
    "i",
    "have",
    "has",
    "how",
    "can",
    "what",
    "do",
    "does",
    "it",
    "this",
    "that"
}


def normalize_text(text: str) -> str:
    """
    Lowercase text and remove non-alphanumeric characters.
    """

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def tokenize(text: str) -> List[str]:
    """
    Convert text into useful search tokens.
    """

    normalized = normalize_text(text)

    return [
        token
        for token in normalized.split()
        if token not in STOP_WORDS
        and len(token) > 1
    ]


class KeywordSearcher:
    """
    Simple metadata-aware keyword fallback search.

    Used only when semantic retrieval confidence is low.
    """

    def __init__(
        self,
        documents_path: Path = DOCUMENTS_PATH
    ):
        with open(
            documents_path,
            "r",
            encoding="utf-8"
        ) as f:
            self.documents = json.load(f)

    def _score_document(
        self,
        query: str,
        document: Dict[str, Any]
    ) -> float:

        query_normalized = normalize_text(query)

        title = normalize_text(
            document.get("title", "")
        )

        text = normalize_text(
            document.get("text", "")
        )

        crop = normalize_text(
            str(document.get("crop", ""))
        )

        category = normalize_text(
            str(document.get("category", ""))
        )

        query_tokens = set(
            tokenize(query)
        )

        title_tokens = set(
            tokenize(title)
        )

        text_tokens = set(
            tokenize(text)
        )

        if not query_tokens:
            return 0.0

        score = 0.0

        # Title overlap gets the highest weight
       

        title_overlap = (
            query_tokens & title_tokens
        )

        score += len(title_overlap) * 4.0

        # Body-text overlap

        text_overlap = (
            query_tokens & text_tokens
        )

        score += len(text_overlap) * 1.0

        # Exact title phrase bonus
        

        if title and title in query_normalized:
            score += 10.0

        # Strong partial disease/title phrase bonus
        
        # Example:
        # "late blight" should strongly favour
        # Tomato Late Blight over Tomato Early Blight.
    

        title_words = title.split()

        if len(title_words) >= 2:

            for length in range(
                len(title_words),
                1,
                -1
            ):
                for start in range(
                    len(title_words) - length + 1
                ):

                    phrase = " ".join(
                        title_words[
                            start:start + length
                        ]
                    )

                    if phrase in query_normalized:
                        score += length * 3.0
                        break

        # Crop/category presence bonus
        

        if crop and crop in query_tokens:
            score += 2.0

        if category and category in query_tokens:
            score += 1.0

        return score

    def search(
        self,
        query: str,
        top_k: int = 3,
        crop_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:

        results = []

        for document in self.documents:

            # Optional crop filter
            

            if crop_filter:

                document_crop = str(
                    document.get("crop", "")
                ).lower()

                if (
                    document_crop
                    != crop_filter.lower()
                ):
                    continue

            # Optional category filter
            

            if category_filter:

                document_category = str(
                    document.get("category", "")
                ).lower()

                if (
                    document_category
                    != category_filter.lower()
                ):
                    continue

            score = self._score_document(
                query,
                document
            )

            if score <= 0:
                continue

            results.append(
                {
                    "id": document.get("id"),
                    "title": document.get("title"),
                    "text": document.get("text"),
                    "crop": document.get("crop"),
                    "category": document.get("category"),
                    "source": document.get("source"),
                    "source_id": document.get(
                        "source_id"
                    ),
                    "region": document.get(
                        "region"
                    ),
                    "season": document.get(
                        "season"
                    ),
                    "keyword_score": score
                }
            )

        results.sort(
            key=lambda item: item[
                "keyword_score"
            ],
            reverse=True
        )

        return results[:top_k]


if __name__ == "__main__":

    searcher = KeywordSearcher()

    results = searcher.search(
        query=(
            "My tomato plants have late blight "
            "with water soaked grey green spots"
        ),
        top_k=3,
        crop_filter="tomato",
        category_filter="disease"
    )

    print("\nKeyword Search Results\n")

    for index, result in enumerate(
        results,
        start=1
    ):

        print(
            f"{index}. "
            f"{result['title']} "
            f"({result['source_id']}) "
            f"score={result['keyword_score']}"
        )