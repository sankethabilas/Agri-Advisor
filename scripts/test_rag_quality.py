from agents.rag.agent import RAGAgent


# 15 representative farmer queries
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

    correct_count = 0

    print("\nRAG Retrieval Quality Test")
    print("=" * 60)

    for index, query in enumerate(test_queries, start=1):

        embedding = agent.encode_query(query)

        results = agent.search(
            query_embedding=embedding,
            top_k=3
        )

        sources, confidence = agent.build_sources(
            results,
            min_score=0.60
        )

        print(f"\nTest {index}")
        print(f"Query: {query}")

        if not sources:
            print("Top Result: No relevant document found")
            print("Score: N/A")
            print("Relevant? NO")

        else:
            top_source = sources[0]

            print(f"Top Result: {top_source['title']}")
            print(f"Source: {top_source['source']}")
            print(f"Score: {top_source['score']:.4f}")

            # Manually inspect the result and change this later
            print("Relevant?: REVIEW")

    print("\n" + "=" * 60)
    print("Review each top-ranked result manually.")
    print("Target: At least 12 out of 15 must be genuinely relevant.")


if __name__ == "__main__":
    main()