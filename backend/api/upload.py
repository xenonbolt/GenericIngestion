from fastapi import APIRouter, UploadFile, File, Form
import tempfile
import os
import base64
import json
from ingestion.pipeline import pipeline
from auth.approval_manager import approval_manager
from auth.audit_manager import audit_manager

router = APIRouter()

@router.post("/analyze-metadata")
async def analyze_metadata(file: UploadFile = File(...)):
    content = await file.read()
    mime = file.content_type or "application/octet-stream"
    try:
        from langchain_core.messages import HumanMessage
        llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        # If it's an image, audio, or video, use multimodal approach
        if "image" in mime or "audio" in mime or "video" in mime:
            if llm_provider == "openai" and ("audio" in mime or "video" in mime):
                ext = os.path.splitext(file.filename)[1]
                extracted_text = pipeline._extract_text_from_media_native(content, mime, file.filename, ext)
                msg = HumanMessage(
                    content=[
                        {"type": "text", "text": f"Analyze the following {mime} file content. Provide a JSON response with exactly these keys: 'summary' (a 2-sentence description), 'category' (one word), and 'tags' (a comma-separated string of 3-5 tags). Output only raw JSON.\n\nContent:\n{extracted_text}"}
                    ]
                )
            else:
                encoded_data = base64.b64encode(content).decode('utf-8')
                msg = HumanMessage(
                    content=[
                        {"type": "text", "text": f"Analyze this {mime} file. Provide a JSON response with exactly these keys: 'summary' (a 2-sentence description), 'category' (one word), and 'tags' (a comma-separated string of 3-5 tags). Output only raw JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded_data}"}}
                    ]
                )
        else:
            # For Text, CSV, PDF, we need to extract text first
            extracted_text = ""
            if mime == "application/pdf":
                extracted_text = pipeline._extract_text_from_pdf(content)
            else:
                extracted_text = content.decode('utf-8', errors='ignore')
                
            # Truncate text to avoid context limits on huge files
            extracted_text = extracted_text[:10000] 
            
            msg = HumanMessage(
                content=[
                    {"type": "text", "text": f"Analyze the following {mime} file content. Provide a JSON response with exactly these keys: 'summary' (a 2-sentence description), 'category' (one word), and 'tags' (a comma-separated string of 3-5 tags). Output only raw JSON.\n\nContent:\n{extracted_text}"}
                ]
            )
            
        resp = pipeline.llm.invoke([msg])
        import re
        json_match = re.search(r'\{.*\}', resp.content, re.DOTALL)
        if json_match:
            metadata = json.loads(json_match.group(0))
        else:
            metadata = json.loads(resp.content)
        return metadata
    except Exception as e:
        print("Metadata analysis error:", e)
        return {"summary": "Error analyzing file", "category": "Error", "tags": ""}

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    summary: str = Form(""),
    category: str = Form(""),
    tags: str = Form(""),
    user_id: str = Form(...),
    role: str = Form(...)
):
    content = await file.read()
    mime = file.content_type or "text/plain"
    
    metadata = {
        "summary": summary,
        "category": category,
        "tags": tags
    }
    
    audit_manager.log_action(user_id, "FILE_UPLOAD_REQUESTED", f"File: {file.filename}, Role: {role}")

    if role == "admin":
        # Direct ingestion
        if "csv" in mime or file.filename.endswith(".csv"):
            doc_id = pipeline.ingest_tabular_file(file.filename, content, mime, metadata)
        else:
            doc_id = pipeline.ingest_unstructured_file(file.filename, content, mime, metadata)
            
        audit_manager.log_action(user_id, "FILE_UPLOAD_APPROVED", f"Auto-approved admin upload: {file.filename}")
        return {"status": "success", "doc_id": doc_id, "message": "File ingested successfully."}
        
    else:
        # Save for approval
        temp_dir = os.path.join(os.getcwd(), "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{user_id}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)
            
        approval_id = approval_manager.add_pending(file_path, file.filename, mime, metadata, user_id)
        return {"status": "pending", "approval_id": approval_id, "message": "Upload submitted for Admin approval."}
