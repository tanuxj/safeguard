import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
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

R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL", "").rstrip("/")
R2_REGION = os.getenv("R2_REGION", "auto")


def _is_r2_enabled() -> bool:
    return bool(
        R2_ENDPOINT_URL and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET_NAME
    )


def _get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name=R2_REGION,
    )


def _build_storage_key(user_id: str, share_token: str, file_name: str) -> str:
    safe_filename = Path(file_name).name
    stem = Path(safe_filename).stem
    suffix = Path(safe_filename).suffix
    unique_suffix = secrets.token_hex(4)
    storage_filename = f"{stem}_{unique_suffix}{suffix}"
    date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    return f"sends/{user_id}/{date_prefix}/{storage_filename}"


def upload_file_for_send(
    *,
    user_id: str,
    share_token: str,
    file_name: str,
    file_bytes: bytes,
    file_mime_type: str | None,
) -> str:
    storage_key = _build_storage_key(user_id, share_token, file_name)
    if _is_r2_enabled():
        try:
            client = _get_r2_client()
            extra_args: dict[str, str] = {}
            if file_mime_type:
                extra_args["ContentType"] = file_mime_type
            client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=storage_key,
                Body=file_bytes,
                **extra_args,
            )
            return storage_key
        except (BotoCoreError, ClientError):
            # Fallback to local storage so uploads still work if R2 is temporarily unavailable.
            pass

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    local_storage_name = f"{share_token}_{Path(file_name).name}"
    file_path = UPLOAD_DIR / local_storage_name
    file_path.write_bytes(file_bytes)
    return str(file_path)


def get_send_file_bytes(file_path: str) -> bytes | None:
    if _is_r2_enabled() and not Path(file_path).exists():
        try:
            client = _get_r2_client()
            response = client.get_object(Bucket=R2_BUCKET_NAME, Key=file_path)
            return response["Body"].read()
        except (BotoCoreError, ClientError, KeyError):
            return None

    local_path = Path(file_path)
    if local_path.exists():
        return local_path.read_bytes()

    if R2_PUBLIC_BASE_URL:
        return None
    return None


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
    stored_file_path = upload_file_for_send(
        user_id=user_id,
        share_token=share_token,
        file_name=safe_filename,
        file_bytes=file_bytes,
        file_mime_type=file_mime_type,
    )

    password_hash = (
        password_hasher.hash_password(access_password) if access_password else None
    )

    return await Send.create(
        user_id=user_id,
        name=name.strip(),
        send_type="file",
        text_to_share="",
        file_name=safe_filename,
        file_path=stored_file_path,
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
