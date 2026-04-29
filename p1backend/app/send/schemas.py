from datetime import datetime

from pydantic import BaseModel, Field


class CreateSendRequest(BaseModel):
    name: str
    text_to_share: str = Field(min_length=1)
    deletion_date: datetime
    who_can_view: str = "Anyone with the link"
    access_password: str | None = None
    limit_views: int | None = None
    private_note: str | None = None


class CreateSendResponse(BaseModel):
    message: str
    send_id: str
    share_link: str


class PublicSendResponse(BaseModel):
    name: str
    text_to_share: str
    deletion_date: datetime
    who_can_view: str
