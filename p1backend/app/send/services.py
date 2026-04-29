import secrets
from pathlib import Path
from datetime import datetime, timezone

from jwt import InvalidTokenError
from app.send.models import Send
from app.send.schemas import CreateSendRequest
from app.utils.jwt import JWTService
from app.utils.passwordHash import PasswordHasher

jwt_service = JWTService(
    secret_key="your_super_secret_key",
    algorithm="HS256",
)
password_hasher = PasswordHasher()
UPLOAD_DIR = Path("uploads/sends")
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def get_access_payload_from_header(authorization: str | None) -> dict | None:
    token = extract_bearer_token(authorization)
    if not token:
        return None

    try:
        payload = jwt_service.decode_token(token)
    except InvalidTokenError:
        return None

    if payload.get("type") != "access":
        return None

    return payload


def build_share_link(token: str) -> str:
    return f"/send/public/{token}"


async def create_text_send(user_id: str, data: CreateSendRequest) -> Send:
    share_token = secrets.token_urlsafe(24)
    password_hash = (
        password_hasher.hash_password(data.access_password)
        if data.access_password
        else None
    )
    return await Send.create(
        user_id=user_id,
        name=data.name.strip(),
        send_type="text",
        text_to_share=data.text_to_share,
        deletion_date=data.deletion_date,
        who_can_view=data.who_can_view,
        password_hash=password_hash,
        limit_views=data.limit_views,
        private_note=data.private_note,
        share_token=share_token,
    )


async def create_file_send(
    user_id: str,
    *,
    name: str,
    deletion_date: datetime,
    who_can_view: str,
    access_password: str | None,
    limit_views: int | None,
    private_note: str | None,
    file_name: str,
    file_mime_type: str | None,
    file_bytes: bytes,
) -> Send:
    share_token = secrets.token_urlsafe(24)
    safe_filename = Path(file_name).name
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    storage_name = f"{share_token}_{safe_filename}"
    file_path = UPLOAD_DIR / storage_name
    file_path.write_bytes(file_bytes)

    password_hash = (
        password_hasher.hash_password(access_password) if access_password else None
    )

    return await Send.create(
        user_id=user_id,
        name=name.strip(),
        send_type="file",
        text_to_share="",
        file_name=safe_filename,
        file_path=str(file_path),
        file_size=len(file_bytes),
        file_mime_type=file_mime_type,
        deletion_date=deletion_date,
        who_can_view=who_can_view,
        password_hash=password_hash,
        limit_views=limit_views,
        private_note=private_note,
        share_token=share_token,
    )


def is_send_expired(send: Send) -> bool:
    return send.deletion_date <= datetime.now(timezone.utc)


def verify_send_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify_password(plain_password, hashed_password)
