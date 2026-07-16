from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_user_service
from app.application.services.user_service import UserService
from app.schemas.user import UserCreate, UserResponse, Token

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    try:
        user = await user_service.create_user(user_in)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    access_token = user_service.create_access_token(user.id)
    return Token(access_token=access_token, token_type="bearer")
