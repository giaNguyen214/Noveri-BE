from fastapi import APIRouter
from models.auth import RegisterRequest, LoginRequest
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(body: RegisterRequest):
    user = AuthService.register(
        email=body.email,
        phone=body.phone,
        password=body.password,
        full_name=body.full_name
    )
    return {
        "message": "User registered successfully",
        "data": user
    }


@router.post("/login")
def login(body: LoginRequest):
    session = AuthService.login(
        email=body.email,
        password=body.password
    )
    return {
        "message": "Login success",
        "session": session
    }
