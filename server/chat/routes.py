from fastapi import APIRouter, Depends, Form

from auth.routes import authenticate
from .chatQuerry import answer_query

router = APIRouter()


@router.post("")
async def chat(
    message: str = Form(...),
    user: dict = Depends(authenticate),  # type: ignore
):
    return await answer_query(message)
