"""FastAPI microservice for Crop Advisory Agent."""

from fastapi import FastAPI

from agents.crop.agent import crop_agent
from orchestrator.schemas import CropAdviceRequest, CropAdviceResponse

app = FastAPI(
    title="Agri-Advisor Crop Advisory Agent",
    description="8-Stage agronomic crop cultivation guidelines backed by DOA Sri Lanka knowledge base",
    version="1.0.0",
)


@app.post("/api/crop/advice", response_model=CropAdviceResponse)
async def get_crop_advice(request: CropAdviceRequest) -> CropAdviceResponse:
    """Generate 8-section crop advisory plan."""
    return crop_agent.get_crop_advice(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agents.crop.main:app", host="0.0.0.0", port=8004, reload=True)
