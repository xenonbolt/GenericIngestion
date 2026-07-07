from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.approval_manager import approval_manager
from auth.audit_manager import audit_manager
from ingestion.pipeline import pipeline
import os

router = APIRouter(prefix="/admin")

# In a real app, these endpoints would use dependency injection to verify the user is an admin.
# For this lab, we trust the frontend UI to only expose these to admins.

@router.get("/approvals")
def get_pending_approvals():
    return approval_manager.get_pending()

@router.post("/approvals/{approval_id}/approve")
def approve_upload(approval_id: str):
    approval = approval_manager.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    try:
        with open(approval["file_path"], "rb") as f:
            content = f.read()
            
        doc_id = pipeline.ingest_unstructured_file(
            approval["filename"], 
            content, 
            approval["mime_type"], 
            approval["metadata"]
        )
        approval_manager.mark_approved(approval_id)
        audit_manager.log_action("admin", "FILE_UPLOAD_APPROVED", f"Approved file: {approval['filename']}")
        os.remove(approval["file_path"]) # cleanup temp file
        return {"status": "success", "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approvals/{approval_id}/reject")
def reject_upload(approval_id: str):
    approval = approval_manager.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    approval_manager.mark_rejected(approval_id)
    audit_manager.log_action("admin", "FILE_UPLOAD_REJECTED", f"Rejected file: {approval['filename']}")
    try:
        os.remove(approval["file_path"])
    except:
        pass
    return {"status": "success"}

@router.get("/audit-logs")
def get_audit_logs():
    return audit_manager.get_logs()

@router.get("/users")
def get_users():
    from auth.user_manager import user_manager
    return user_manager.get_all_users()

class RoleUpdateRequest(BaseModel):
    role: str

@router.post("/users/{username}/role")
def update_user_role(username: str, req: RoleUpdateRequest):
    from auth.user_manager import user_manager
    if req.role not in ["admin", "basic", "risk-manager"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    success = user_manager.update_user_role(username, req.role)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or role unchanged")
    
    audit_manager.log_action("admin", "USER_ROLE_UPDATED", f"Changed role of {username} to {req.role}")
    return {"status": "success", "message": f"Role updated to {req.role}"}


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str

@router.post("/users")
def create_user(req: CreateUserRequest):
    from auth.user_manager import user_manager
    if req.role not in ["admin", "basic", "risk-manager"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    result = user_manager.create_user(req.username, req.password, req.role)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    audit_manager.log_action("admin", "USER_CREATED", f"Created user {req.username} with role {req.role}")
    return {"status": "success", "message": f"User {req.username} created with role {req.role}"}
