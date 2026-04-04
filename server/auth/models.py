from pydantic import BaseModel, Field
from typing import Optional

class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password:str = Field(..., min_length=6)
    role: str