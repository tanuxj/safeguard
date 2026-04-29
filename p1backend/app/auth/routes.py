from fastapi import APIRouter
from pydantic import BaseModel

from .schemas import UserSignupData, UserLoginData
from app.users.models import User
from app.utils.jwt import JWTService
from app.utils.passwordHash import PasswordHasher

password_hasher = PasswordHasher()

jwt_service = JWTService(
    secret_key="your_super_secret_key",  # move to .env later
    algorithm="HS256",
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register")
async def register(user_data: UserSignupData):
    first_name = user_data.firstName
    last_name = user_data.lastName
    email = user_data.email
    password = user_data.password

    if not first_name or not last_name or not email or not password:
        return {"message": "all fields are required"}

    # check if user already exists
    existing_user = await User.filter(email=email).first()

    if existing_user:
        return {"message": "email already registered"}

    # hash password before saving
    hashed_password = password_hasher.hash_password(password)

    # save user to database
    user = await User.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hashed_password,
    )

    # create tokens
    access_token = jwt_service.create_access_token(
        user_id=str(user.id),
        email=user.email,
    )

    refresh_token = jwt_service.create_refresh_token(
        user_id=str(user.id),
        email=user.email,
    )

    print(f"User registered successfully: {email}")

    return {
        "message": "registration successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login")
async def login(user_data: UserLoginData):
    email = user_data.email
    password = user_data.password

    if not email or not password:
        return {"message": "email and password are required"}

    # fetch user from database
    user = await User.filter(email=email).first()

    if not user:
        return {"message": "user not found"}

    # verify password
    is_valid = password_hasher.verify_password(
        password,
        user.password,
    )

    if not is_valid:
        return {"message": "invalid credentials"}

    # create tokens
    access_token = jwt_service.create_access_token(
        user_id=str(user.id),
        email=user.email,
    )

    refresh_token = jwt_service.create_refresh_token(
        user_id=str(user.id),
        email=user.email,
    )

    print(f"Login successful for: {email}")

    return {
        "message": "login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_access_token(data: RefreshTokenRequest):
    payload = jwt_service.verify_refresh_token(data.refresh_token)

    if not payload:
        return {"message": "invalid or expired refresh token"}

    access_token = jwt_service.create_access_token(
        user_id=str(payload["sub"]),
        email=payload["email"],
    )

    return {
        "message": "access token refreshed",
        "access_token": access_token,
        "token_type": "bearer",
    }
