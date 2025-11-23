from .api import Api
from .base_perms_model import BasePermsModel as BaseModel
from .user_models import User, UserRole, Domain, Token, UserSetting, current_user, get_current_user_id
from .perms_blueprint import PermsBlueprintMixin

from crud import CRUDBlueprint as CRUDBlueprintBase


class CRUDBlueprint(CRUDBlueprintBase, PermsBlueprintMixin):
    """CRUD Blueprint with permission annotations."""

    pass
