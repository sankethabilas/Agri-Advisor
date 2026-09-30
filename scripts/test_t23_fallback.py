import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from agents.rag.agent import RAGAgent
from orchestrator.schemas import RagRetrieveRequest


print("=" * 70)
print("T-23 Keyword Fallback Test")
print("=" * 70)


# Test 1 - Normal semantic retrieval


agent = RAGAgent(
    fallback_threshold=0.60
)


semantic_request = RagRetrieveRequest(
    query=(
        "How can I control bacterial "
        "leaf blight in rice?"
    ),
    top_k=3,
    crop_filter="rice",
    category_filter="disease",
    min_score=0.50,
)


semantic_response = agent.retrieve(
    semantic_request
)


print("\n--- Normal Retrieval Test ---")

print(
    "Top similarity:",
    round(
        agent.last_top_similarity,
        4
    )
)

print(
    "Retrieval method:",
    agent.last_retrieval_method
)

print(
    "Sources returned:",
    len(
        semantic_response.sources
    )
)


assert (
    len(
        semantic_response.sources
    )
    > 0
)

assert agent.last_retrieval_method in {
    "semantic",
    "keyword_fallback",
}


# Test 2 - Forced keyword fallback
#
# Threshold 0.99 is deliberately high so that we
# deterministically exercise the fallback path.

fallback_agent = RAGAgent(
    fallback_threshold=0.99
)


fallback_request = RagRetrieveRequest(
    query=(
        "My tomato plants have late blight "
        "with water soaked grey green spots"
    ),
    top_k=3,
    crop_filter="tomato",
    category_filter="disease",
    min_score=0.50,
)


fallback_response = (
    fallback_agent.retrieve(
        fallback_request
    )
)


print("\n--- Forced Fallback Test ---")

print(
    "Semantic top similarity:",
    round(
        fallback_agent.last_top_similarity,
        4
    )
)

print(
    "Retrieval method:",
    fallback_agent.last_retrieval_method
)

print("\nReturned sources:")

for index, source in enumerate(
    fallback_response.sources,
    start=1,
):
    print(
        f"{index}. "
        f"{source.title} "
        f"({source.source_id})"
    )


assert (
    fallback_agent.last_retrieval_method
    ==
    "keyword_fallback"
), (
    "Keyword fallback did not trigger"
)


assert fallback_response.sources, (
    "Keyword fallback returned no sources"
)


top_source = (
    fallback_response.sources[0]
)


assert (
    top_source.source_id
    ==
    "T-D-003"
), (
    "Expected Tomato Late Blight "
    "T-D-003 as top fallback result, "
    f"got {top_source.source_id}"
)


print("\n✓ Keyword fallback triggered")
print(
    "✓ Tomato Late Blight ranked first"
)


print("\n" + "=" * 70)
print("T-23 KEYWORD FALLBACK TEST PASSED")
print("=" * 70)