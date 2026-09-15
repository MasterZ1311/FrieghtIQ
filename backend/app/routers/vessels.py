"""
Vessel Recommendation Router
============================
Endpoints:
- POST /api/vessel/recommend
- POST /api/vessels/recommend
- GET  /api/vessels/list
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import VesselRecommendRequest, VesselRecommendResponse
from app.services import recommend_vessels

router = APIRouter(tags=["Vessel Recommendation"])


@router.post("/api/vessel/recommend", response_model=VesselRecommendResponse, summary="Recommend optimal vessel class")
@router.post("/api/vessels/recommend", response_model=VesselRecommendResponse, include_in_schema=False)
def recommend(req: VesselRecommendRequest, db: Session = Depends(get_db)):
    """
    Evaluates vessel candidates against cargo parcel, draft limits, and economics.
    """
    try:
        result = recommend_vessels(
            db=db,
            origin=req.origin,
            destination=req.destination,
            commodity=req.commodity,
            cargo_mt=req.cargo_mt or 70000.0,
            budget_usd_per_mt=req.budget_usd_per_mt,
        )
        return VesselRecommendResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Vessel recommendation failed: {str(e)}")


@router.get("/api/vessels/list", summary="Reference vessel class specifications")
@router.get("/api/vessel/list", include_in_schema=False)
def list_vessels():
    """Returns vessel class reference data."""
    from app.seed.seed_data import VESSELS
    return {"vessels": VESSELS}
