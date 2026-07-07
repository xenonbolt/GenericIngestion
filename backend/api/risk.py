from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from risk_engine.analyzer import analyze_risk
from auth.user_manager import user_manager

router = APIRouter(prefix="/api/risk")

class RiskAnalyzeRequest(BaseModel):
    customer_id: str
    source_data: str

@router.post("/analyze")
async def analyze_customer_risk(request: RiskAnalyzeRequest):
    try:
        # Analyze the provided data
        risk_profile = await analyze_risk(request.source_data)
        
        # Save to DB
        user_manager.update_user_risk_profile(request.customer_id, risk_profile)
        
        return {"status": "success", "risk_profile": risk_profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
