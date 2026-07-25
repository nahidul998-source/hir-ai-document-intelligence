from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_user_service
from app.application.services.user_service import UserService
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.advanced_rate_limiter import rate_limit_dependency
from pydantic import BaseModel

router = APIRouter()


@router.post("/register", response_model=UserResponse, dependencies=[Depends(rate_limit_dependency)])
async def register(
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    try:
        user = await user_service.create_user(user_in)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit_dependency)])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Login attempt for: {form_data.username}")
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    logger.info(f"Login result: {user}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    access_token = user_service.create_access_token(user.id)
    return Token(access_token=access_token, token_type="bearer")


class RefreshRequest(BaseModel):
    token: str

@router.post("/refresh", response_model=Token, dependencies=[Depends(rate_limit_dependency)])
async def refresh_token(
    request: RefreshRequest,
    user_service: UserService = Depends(get_user_service)
):
    user_id = user_service.verify_access_token(request.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = user_service.create_access_token(user_id)
    return Token(access_token=access_token, token_type="bearer")
