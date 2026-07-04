from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.user_manager import user_manager
from auth.audit_manager import audit_manager

router = APIRouter(prefix="/auth")

class AuthRequest(BaseModel):
    username: str
    password: str

@router.post("/signup")
def signup(req: AuthRequest):
    res = user_manager.signup(req.username, req.password)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    audit_manager.log_action(req.username, "USER_SIGNUP", f"Role assigned: {res['role']}")
    return {"message": "Signup successful"}

@router.post("/login")
def login(req: AuthRequest):
    res = user_manager.login(req.username, req.password)
    if not res:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    audit_manager.log_action(req.username, "USER_LOGIN")
    return res
