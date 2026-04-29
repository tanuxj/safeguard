from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError


class JWTService:
    ACCESS_TOKEN_EXPIRE_HOURS = 1
    REFRESH_TOKEN_EXPIRE_DAYS = 11

    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, user_id: str, email: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=self.ACCESS_TOKEN_EXPIRE_HOURS
        )

        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "access",
            "exp": expire,
        }

        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

    def create_refresh_token(self, user_id: str, email: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.REFRESH_TOKEN_EXPIRE_DAYS
        )

        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "refresh",
            "exp": expire,
        }

        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

    def decode_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
        )

    def verify_refresh_token(self, token: str) -> dict | None:
        try:
            payload = self.decode_token(token)
            if payload.get("type") != "refresh":
                return None
            return payload
        except InvalidTokenError:
            return None
