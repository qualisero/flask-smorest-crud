"""User schemas."""

from marshmallow import fields

from ..sqla.base_model import BaseSchema
from .user_models import User


class UserSchema(User.Schema):
    """Public user schema - extends auto-generated schema."""

    password = fields.Str(required=True, load_only=True)


class UserLoginSchema(UserSchema):
    """Schema for user login."""

    class Meta:
        fields = ("email", "password")


class TokenSchema(BaseSchema):
    """Schema for JWT token response."""

    access_token = fields.Str(required=True)
    token_type = fields.Str(dump_default="bearer")
