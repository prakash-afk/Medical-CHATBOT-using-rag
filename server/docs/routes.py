from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from auth.routes import authenticate
from .vectorstore import load_vectorStore
import uuid
import traceback

router = APIRouter()
@router.post("/upload-docs")
async def upload_docs(
    user: dict = Depends(authenticate), # type: ignore
    files:list[UploadFile]=File(...),
    role:str=Form("all")
):
    if user["role"] not in {"admin", "doctor"}:
        raise HTTPException(status_code=403,detail="Only admin or doctor can upload documents")
    role = "all"
    doc_id=str(uuid.uuid4())
    try:
        result = await load_vectorStore(files,role,doc_id)
    except Exception as exc:
        message = str(exc)
        print("Document upload failed:")
        traceback.print_exc()
        if "RESOURCE_EXHAUSTED" in message or "quota" in message.lower():
            raise HTTPException(
                status_code=429,
                detail="Embedding quota is temporarily exhausted. Please wait a bit and try uploading again.",
            ) from exc
        raise HTTPException(
            status_code=500,
            detail=f"Document upload failed: {message}",
        ) from exc
    return {
        "message": f"Uploaded {len(files)} files successfully with doc_id {doc_id} and role {role}",
        "doc_id": result["doc_id"],
        "accessible_to": "all users",
        "chunk_count": result["chunk_count"],
        "index_name": result["index_name"],
    }
