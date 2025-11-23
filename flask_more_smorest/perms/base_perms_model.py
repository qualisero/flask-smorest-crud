from contextlib import contextmanager

from flask import has_request_context
from flask_jwt_extended import verify_jwt_in_request, exceptions
from werkzeug.exceptions import Unauthorized

from error.exceptions import ForbiddenError, UnauthorizedError
from sqla import db, BaseModel


class BasePermsModel(BaseModel):
    """Permission-aware Base model for all models."""

    __abstract__ = True
    perms_disabled = False

    def __init__(self, **kwargs):
        """Initialize the model after checking that all sub fields can be created."""

        self.check_create(kwargs.values())
        super().__init__(**kwargs)

    @classmethod
    @contextmanager
    def bypass_perms(cls_self):  # type: ignore
        """Context manager to bypass permissions for the class."""
        original = cls_self.perms_disabled
        cls_self.perms_disabled = True
        try:
            yield
        finally:
            cls_self.perms_disabled = original

    def can_write(self):
        """Does current user have write permission on object."""

        if self.perms_disabled or not has_request_context():
            return True

        is_admin = getattr(self, "is_admin", False)
        is_role_instance = type(self).__name__ == "UserRole"
        if not is_role_instance and not is_admin and self.is_current_user_admin():
            return True

        try:
            if self.id is None:
                return self._can_create()
            return self._can_write()
        except RuntimeError:
            raise UnauthorizedError("User must be authenticated")
        except Exception as e:
            print("DEBUG: can_write() ***EXCEPTION:", e)
            pass

        return False

    def can_read(self):
        """Does current user have read permissions on object."""

        if self.perms_disabled or not has_request_context():
            return True

        if self.id is None or self.is_current_user_admin():
            return True
        try:
            if self._can_read():
                return True
        except RuntimeError:
            raise UnauthorizedError("User must be authenticated")
        except Exception as e:
            print("DEBUG: can_read() ***EXCEPTION:", e)
            pass

        return False

    def can_create(self):
        """Can current user create object."""

        if self.perms_disabled or not has_request_context():
            return True
        is_admin = getattr(self, "is_admin", False)
        is_role_instance = type(self).__name__ == "UserRole"
        if not is_role_instance and not is_admin and self.is_current_user_admin():
            return True

        return self._can_create()

    def _can_write(self):
        """Permission helper: override in subclasses."""
        return False

    def _can_create(self):
        """Permission helper: override in subclasses."""
        return True  # adding new records is allowed by default

    def _can_read(self):
        """Permission helper: override in subclasses."""
        return self._can_write()

    @classmethod
    def is_current_user_admin(cls):
        from .user_models import current_user

        try:
            verify_jwt_in_request()
            if current_user.is_admin:
                return True
        except exceptions.JWTExtendedException:
            return False
        except Unauthorized:
            return False

        return False

    def check_create(self, val):
        """Recursively check that all BaseModel instances can be created."""
        for x in val:
            if isinstance(x, BasePermsModel):
                if x.id is None and not x.can_create():
                    raise ForbiddenError(f"User not allowed to create resource: {x}")
            elif isinstance(x, list):
                self.check_create(x)
