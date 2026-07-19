from pydantic import BaseModel, Field
from typing import List, Dict, Any


class PredictionRequest(BaseModel):
    district: str
    built_up_area_sqft: float = Field(..., gt=0)
    plot_size_cents: float = Field(..., gt=0)
    bedrooms: int = Field(..., ge=1)
    bathrooms: int = Field(..., ge=1)
    floors: int = Field(..., ge=1)
    parking_spaces: int = Field(..., ge=0)
    balconies: int = Field(..., ge=0)
    kitchen_type: str
    quality: str
    roof_type: str
    flooring: str
    budget: float = Field(..., gt=0)
    addons: List[str] = []


class StageCost(BaseModel):
    stage: str
    percentage: float
    cost: float


class Recommendation(BaseModel):
    type: str
    title: str
    description: str
    priority: str
    estimated_cost_impact: str


class BudgetAnalysis(BaseModel):
    status: str
    surplus: float
    deficit: float
    utilization: float


class AddonCost(BaseModel):
    name: str
    cost: float


class PredictionResponse(BaseModel):
    predicted_cost: float
    cost_range: Dict[str, float]
    model_accuracy: float
    cost_per_sqft: float
    house_category: str
    construction_time: str
    health_score: int
    budget: BudgetAnalysis
    stage_breakdown: List[StageCost]
    recommendations: List[Recommendation]
    addons: Dict[str, Any]