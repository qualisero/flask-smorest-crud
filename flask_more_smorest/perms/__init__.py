"""Permissions module for Flask-More-Smorest.

This module provides the permissions system including the Api with auth,
BasePermsModel with permission checks, user models, and PermsBlueprintMixin.
"""

from .api import Api
from .base_perms_model import BasePermsModel
from .jwt import init_jwt
from .model_mixins import (
    HasUserMixin,
    ProfileMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UserOwnershipMixin,
)
from .perms_blueprint import PermsBlueprint, PermsBlueprintMixin
from .user_blueprints import UserBlueprint, user_bp
from .user_models import (
    Domain,
    Token,
    User,
    UserRole,
    UserSetting,
    current_user,
    get_current_user,
    get_current_user_id,
)
from .user_schemas import UserSchema

__all__ = [
    "Api",
    "BasePermsModel",
    "User",
    "UserRole",
    "Domain",
    "Token",
    "UserSetting",
    "current_user",
    "UserSchema",
    "get_current_user",
    "get_current_user_id",
    "HasUserMixin",
    "UserOwnershipMixin",
    "ProfileMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "PermsBlueprintMixin",
    "PermsBlueprint",
    "UserBlueprint",
    "user_bp",
    "init_jwt",
]
