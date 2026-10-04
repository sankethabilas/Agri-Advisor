import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

from agents.rag.agent import RAGAgent
from orchestrator.schemas import RagRetrieveRequest


# Original 15 representative farmer queries from T-11.
# Keep these unchanged so T-23 can be compared fairly
# against the original baseline.

test_queries = [
    "My rice leaves have yellow spots",
    "Rice leaves have narrow brown lesions",
    "How can I control bacterial leaf blight in rice?",
    "What causes rice leaf scald?",
    "What are the symptoms of brown spot disease in rice?",
    "My chilli plants have curled leaves",
    "How do I manage fungal diseases in chilli?",
    "What causes bacterial wilt in chilli?",
    "How should chilli be cultivated?",
    "My tomato plants are wilting suddenly",
    "What are the symptoms of tomato early blight?",
    "How do I manage tomato late blight?",
    "Tomato leaves are curling and yellowing",
    "What are recommended varieties of big onion?",
    "How should I manage diseases in tomato?"
]


def main():

    agent = RAGAgent()

    print()
    print("=" * 75)
    print("T-23 Retrieval Quality Evaluation")
    print("=" * 75)

    print()
    print("T-11 Baseline:")
    print("Correct top-ranked results : 14 / 15")
    print("Top-1 retrieval accuracy   : 93.33%")

    print()
    print("=" * 75)

    for index, query in enumerate(
        test_queries,
        start=1
    ):

        request = RagRetrieveRequest(
            query=query,
            top_k=3,
            min_score=0.60,
        )

        response = agent.retrieve(
            request
        )

        print()
        print(f"Test {index}")
        print(f"Query: {query}")

        if not response.sources:

            print(
                "Top Result: "
                "No relevant document found"
            )

            print("Source ID: N/A")
            print("Score: N/A")

        else:

            top_source = (
                response.sources[0]
            )

            print(
                f"Top Result: "
                f"{top_source.title}"
            )

            print(
                f"Source ID: "
                f"{top_source.source_id}"
            )

            print(
                f"Source: "
                f"{top_source.source}"
            )

            if response.confidence:

                print(
                    f"Score: "
                    f"{response.confidence[0]:.4f}"
                )

        print(
            "Retrieval Method:",
            agent.last_retrieval_method
        )

        print(
            "Semantic Top Similarity:",
            f"{agent.last_top_similarity:.4f}"
        )

        print(
            "Relevant?: REVIEW"
        )

    print()
    print("=" * 75)
    print(
        "Review each top-ranked result "
        "using the same relevance criteria as T-11."
    )
    print(
        "Record the number of correct "
        "top-ranked documents out of 15."
    )
    print("=" * 75)


if __name__ == "__main__":
    main()