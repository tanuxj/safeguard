import uuid

from tortoise import fields
from tortoise.models import Model


class Send(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField(
        "models.User", related_name="sends", on_delete=fields.CASCADE
    )

    name = fields.CharField(max_length=255)
    send_type = fields.CharField(max_length=16, default="text")
    text_to_share = fields.TextField()
    file_name = fields.CharField(max_length=255, null=True)
    file_path = fields.CharField(max_length=500, null=True)
    file_size = fields.BigIntField(null=True)
    file_mime_type = fields.CharField(max_length=255, null=True)
    deletion_date = fields.DatetimeField()
    who_can_view = fields.CharField(max_length=64, default="Anyone with the link")
    password_hash = fields.CharField(max_length=255, null=True)
    limit_views = fields.IntField(null=True)
    view_count = fields.IntField(default=0)
    private_note = fields.TextField(null=True)
    share_token = fields.CharField(max_length=128, unique=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "sends"
