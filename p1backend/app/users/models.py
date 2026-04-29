import uuid

from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=255)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"
