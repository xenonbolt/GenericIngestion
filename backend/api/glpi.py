from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
from ingestion.glpi_sync import glpi_sync_manager
from auth.audit_manager import audit_manager

router = APIRouter(prefix="/admin/glpi")

class GLPISyncRequest(BaseModel):
    glpi_url: str = ""
    app_token: str = ""
    user_token: str = ""
    use_mock: bool = True

@router.post("/sync")
async def trigger_glpi_sync(req: GLPISyncRequest):
    try:
        # Perform Sync
        result = glpi_sync_manager.run_sync(
            glpi_url=req.glpi_url,
            app_token=req.app_token,
            user_token=req.user_token,
            use_mock=req.use_mock
        )
        
        # Log action in system audit trails
        mode = "Mock Sandbox" if result.get("use_mock") else "Remote Live"
        audit_manager.log_action(
            "admin", 
            "GLPI_SYNC_TRIGGERED", 
            f"GLPI sync executed in {mode} mode. Computers: {result.get('computers_synced')}, Tickets: {result.get('tickets_synced')}"
        )
        
        return result
    except Exception as e:
        audit_manager.log_action("admin", "GLPI_SYNC_FAILED", f"GLPI sync execution failed. Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_glpi_status():
    status_path = os.path.join(os.getcwd(), "data", "glpi_status.json")
    if os.path.exists(status_path):
        try:
            with open(status_path, "r") as f:
                return json.load(f)
        except Exception as e:
            return {"status": "error", "message": f"Failed to read GLPI status file: {str(e)}"}
    else:
        return {"status": "never_synced", "message": "GLPI ITAM records have not been synced yet."}
