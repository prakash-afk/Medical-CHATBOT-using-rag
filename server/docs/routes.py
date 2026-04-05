from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from auth.routes import authenticate
from .vectorstore import load_vectorStore
import uuid

router = APIRouter()
@router.post("/upload-docs")
async def upload_docs(
    user: dict = Depends(authenticate), # type: ignore
    files:list[UploadFile]=File(...),
    role:str=Form(...)
):
    if user['role']!="admin":
        raise HTTPException(status_code=403,detail="Only admin can upload documents")
    doc_id=str(uuid.uuid4())
    await load_vectorStore(files,role,doc_id)
    return {"message":f"Uploaded {len(files)} files successfully with doc_id {doc_id} and role {role}"}