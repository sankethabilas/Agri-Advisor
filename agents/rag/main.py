"""FastAPI microservice for RAG / Information Retrieval Agent."""

from fastapi import Depends, FastAPI

from agents.rag.agent import rag_agent
from orchestrator.schemas import RagRetrieveRequest, RagRetrieveResponse
from orchestrator.security import get_current_user

app = FastAPI(
    title="Agri Advisor RAG Agent",
    description="Knowledge Retrieval microservice querying indexed Department of Agriculture documents in ChromaDB",
    version="1.0.0",
)


@app.post("/api/rag/retrieve", response_model=RagRetrieveResponse)
async def retrieve(
    request: RagRetrieveRequest,
    current_user: str = Depends(get_current_user),
) -> RagRetrieveResponse:
    """Retrieve grounded knowledge passages from ChromaDB."""
    return rag_agent.retrieve(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agents.rag.main:app", host="0.0.0.0", port=8003, reload=True)