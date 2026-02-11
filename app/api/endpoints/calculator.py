from fastapi import APIRouter
from pydantic import BaseModel
from app.core.physics import calculate_crosswind

router = APIRouter()

class ManualCalcRequest(BaseModel):
    rwy_heading: int
    wind_dir: int
    wind_speed: int

@router.post("/calculate-manual")
async def manual_calc(data: ManualCalcRequest):
    result = calculate_crosswind(data.rwy_heading, data.wind_dir, data.wind_speed)
    return {"status": "success", "crosswind": result}