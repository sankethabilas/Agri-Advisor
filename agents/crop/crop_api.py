from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from agents.crop.crop_agent import CropAdvisoryAgent


app = FastAPI(
    title="Agri Advisor Crop Advisory Agent",
    version="1.0.0"
)

crop_agent = CropAdvisoryAgent()


class CropAdviceRequest(BaseModel):
    crop: str
    location: Optional[str] = None
    season: Optional[str] = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "agent": "crop_advisory"
    }


@app.post("/api/crop/advice")
def get_crop_advice(
    request: CropAdviceRequest
):
    return crop_agent.get_advisory(
        crop=request.crop,
        location=request.location,
        season=request.season
    )