import os

from fastapi import APIRouter, Header, Request
from fastapi import File, Form, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response

from app.send.models import Send
from app.send.schemas import CreateSendRequest, UpdateSendDeletionDateRequest
from app.send.services import (
    build_share_link,
    create_text_send,
    create_file_send,
    get_send_file_bytes,
    get_access_payload_from_header,
    is_send_expired,
    MAX_FILE_SIZE_BYTES,
    verify_send_password,
)

router = APIRouter(prefix="/send", tags=["Send"])
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")


@router.post("/text")
async def create_send(
    data: CreateSendRequest,
    request: Request,
    authorization: str | None = Header(default=None),
):
    payload = get_access_payload_from_header(authorization)
    if not payload:
        return {"message": "unauthorized"}

    if data.deletion_date.tzinfo is None:
        return {"message": "deletion date must include timezone"}

    if (
        data.who_can_view == "Anyone with a password set by you"
        and not data.access_password
    ):
        return {"message": "password is required"}

    send = await create_text_send(str(payload["sub"]), data)
    absolute_link = str(request.base_url).rstrip("/") + build_share_link(
        send.share_token
    )

    return {
        "message": "send created successfully",
        "send_id": str(send.id),
        "share_link": absolute_link,
    }


@router.get("/mine")
async def list_my_sends(
    request: Request,
    authorization: str | None = Header(default=None),
):
    payload = get_access_payload_from_header(authorization)
    if not payload:
        return {"message": "unauthorized"}

    sends = await Send.filter(user_id=str(payload["sub"])).order_by("-created_at").all()

    base_url = str(request.base_url).rstrip("/")
    return {
        "sends": [
            {
                "id": str(send.id),
                "name": send.name,
                "send_type": send.send_type,
                "deletion_date": send.deletion_date,
                "share_token": send.share_token,
                "share_link": f"{base_url}/send/public/{send.share_token}",
            }
            for send in sends
        ]
    }


@router.post("/file")
async def create_file_send_route(
    request: Request,
    authorization: str | None = Header(default=None),
    name: str = Form(...),
    deletion_date: str = Form(...),
    who_can_view: str = Form("Anyone with the link"),
    access_password: str | None = Form(default=None),
    limit_views: int | None = Form(default=None),
    private_note: str | None = Form(default=None),
    upload: UploadFile = File(...),
):
    payload = get_access_payload_from_header(authorization)
    if not payload:
        return {"message": "unauthorized"}

    from datetime import datetime

    parsed_deletion_date = datetime.fromisoformat(deletion_date.replace("Z", "+00:00"))
    if parsed_deletion_date.tzinfo is None:
        return {"message": "deletion date must include timezone"}

    if who_can_view == "Anyone with a password set by you" and not access_password:
        return {"message": "password is required"}

    file_bytes = await upload.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return {"message": "file size must be 50MB or less"}

    send = await create_file_send(
        str(payload["sub"]),
        name=name,
        deletion_date=parsed_deletion_date,
        who_can_view=who_can_view,
        access_password=access_password,
        limit_views=limit_views,
        private_note=private_note,
        file_name=upload.filename or "uploaded-file",
        file_mime_type=upload.content_type,
        file_bytes=file_bytes,
    )
    absolute_link = str(request.base_url).rstrip("/") + build_share_link(
        send.share_token
    )

    return {
        "message": "file send created successfully",
        "send_id": str(send.id),
        "share_link": absolute_link,
    }


@router.delete("/{send_id}")
async def delete_send(
    send_id: str,
    authorization: str | None = Header(default=None),
):
    payload = get_access_payload_from_header(authorization)
    if not payload:
        return {"message": "unauthorized"}

    send = await Send.filter(id=send_id, user_id=str(payload["sub"])).first()
    if not send:
        return {"message": "send not found"}

    await send.delete()
    return {"message": "send deleted successfully"}


@router.patch("/{send_id}/deletion-date")
async def update_send_deletion_date(
    send_id: str,
    data: UpdateSendDeletionDateRequest,
    authorization: str | None = Header(default=None),
):
    payload = get_access_payload_from_header(authorization)
    if not payload:
        return {"message": "unauthorized"}

    if data.deletion_date.tzinfo is None:
        return {"message": "deletion date must include timezone"}

    send = await Send.filter(id=send_id, user_id=str(payload["sub"])).first()
    if not send:
        return {"message": "send not found"}

    send.deletion_date = data.deletion_date
    await send.save(update_fields=["deletion_date", "updated_at"])
    return {"message": "send deletion date updated successfully"}


@router.get("/public/{share_token}")
async def redirect_public_send(share_token: str):
    return RedirectResponse(
        url=f"{FRONTEND_BASE_URL}/send/public/{share_token}", status_code=307
    )


@router.get("/public-data/{share_token}")
async def get_public_send(
    share_token: str,
    authorization: str | None = Header(default=None),
    password: str | None = None,
):
    send = await Send.filter(share_token=share_token).first()
    if not send:
        return {"message": "send not found"}

    payload = get_access_payload_from_header(authorization)
    is_owner = bool(payload and str(payload.get("sub")) == str(send.user_id))

    if (not is_owner) and is_send_expired(send):
        return {"message": "send expired"}

    if (
        (not is_owner)
        and send.limit_views is not None
        and send.view_count >= send.limit_views
    ):
        return {"message": "view limit reached"}

    if (not is_owner) and send.password_hash:
        if not password:
            return {"message": "password required"}
        if not verify_send_password(password, send.password_hash):
            return {"message": "invalid password"}

    if not is_owner:
        send.view_count += 1
        await send.save(update_fields=["view_count"])

    return {
        "send_type": send.send_type,
        "name": send.name,
        "text_to_share": send.text_to_share,
        "file_name": send.file_name,
        "file_size": send.file_size,
        "file_mime_type": send.file_mime_type,
        "deletion_date": send.deletion_date,
        "who_can_view": send.who_can_view,
    }


@router.get("/public-file/{share_token}")
async def download_public_file(
    share_token: str,
    authorization: str | None = Header(default=None),
    password: str | None = None,
):
    send = await Send.filter(share_token=share_token).first()
    if not send or send.send_type != "file" or not send.file_path or not send.file_name:
        return {"message": "file send not found"}

    payload = get_access_payload_from_header(authorization)
    is_owner = bool(payload and str(payload.get("sub")) == str(send.user_id))

    if (not is_owner) and is_send_expired(send):
        return {"message": "send expired"}
    if (
        (not is_owner)
        and send.limit_views is not None
        and send.view_count >= send.limit_views
    ):
        return {"message": "view limit reached"}
    if (not is_owner) and send.password_hash:
        if not password:
            return {"message": "password required"}
        if not verify_send_password(password, send.password_hash):
            return {"message": "invalid password"}

    if not is_owner:
        send.view_count += 1
        await send.save(update_fields=["view_count"])

    file_bytes = get_send_file_bytes(send.file_path)
    if file_bytes is None:
        return {"message": "file not found"}

    headers = {"Content-Disposition": f'attachment; filename="{send.file_name}"'}
    return Response(
        content=file_bytes,
        media_type=send.file_mime_type or "application/octet-stream",
        headers=headers,
    )
