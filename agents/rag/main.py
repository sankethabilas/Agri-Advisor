from fastapi import FastAPI

from agents.rag.agent import RAGAgent
from orchestrator.schemas import (
    RagRetrieveRequest,
    RagRetrieveResponse,
    RagMetadata
)


app = FastAPI(
    title="Agri Advisor RAG Agent",
    version="1.0.0"
)

# Initialize the RAG agent once when the service starts
rag_agent = RAGAgent()


@app.post(
    "/api/rag/retrieve",
    response_model=RagRetrieveResponse
)
def retrieve(request: RagRetrieveRequest):

    # 1. Convert the farmer query into an embedding
    query_embedding = rag_agent.encode_query(
        request.query
    )

    # 2. Search ChromaDB
    results = rag_agent.search(
        query_embedding=query_embedding,
        top_k=request.top_k,
        crop_filter=request.crop_filter,
        category_filter=request.category_filter
    )

    # 3. Build sources and apply minimum similarity threshold
    sources, confidence = rag_agent.build_sources(
        results,
        min_score=request.min_score
    )

    # 4. Explicitly handle the empty-result case
    if not sources:
        return RagRetrieveResponse(
            context="",
            sources=[],
            confidence=[],
            metadata=RagMetadata(
                total_chunks_retrieved=0,
                query_embedding_model="all-MiniLM-L6-v2",
                vector_distance_metric="cosine"
            )
        )

    # 5. Assemble retrieved passages into one context
    context = rag_agent.build_context(
        sources
    )

    # 6. Return the final RAG response
    return RagRetrieveResponse(
        context=context,
        sources=sources,
        confidence=confidence,
        metadata=RagMetadata(
            total_chunks_retrieved=len(sources),
            query_embedding_model="all-MiniLM-L6-v2",
            vector_distance_metric="cosine"
        )
    )