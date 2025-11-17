from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone: Optional[str] = None
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
