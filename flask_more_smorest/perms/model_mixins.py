from typing import TYPE_CHECKING
import uuid
import datetime as dt

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user_models import User, get_current_user_id, current_user


class HasUserMixin:
    """Mixin to add user ID to a model."""

    @declared_attr
    def user_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            default=get_current_user_id,
        )

    @declared_attr
    def user(cls) -> Mapped["User"]:
        return relationship(
            "User",
            lazy="joined",
            foreign_keys=[getattr(cls, "user_id")],
        )


class UserCanReadWriteMixin(HasUserMixin):
    """Mixin to add user write permissions."""

    def _can_write(self):
        """User can write if they are the owner of the object."""
        return self.user_id == current_user.id

    def _can_read(self):
        """User can read if they are the owner of the object."""
        return self.user_id == current_user.id


# Commonly used mixins for extending User models
class TimestampMixin:
    """Mixin adding additional timestamp fields."""

    last_login_at: Mapped[sa.DateTime | None] = mapped_column(sa.DateTime(), nullable=True)
    email_verified_at: Mapped[sa.DateTime | None] = mapped_column(sa.DateTime(), nullable=True)


class ProfileMixin:
    """Mixin adding basic profile fields."""

    first_name: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    last_name: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    display_name: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)

    @property
    def full_name(self) -> str:
        """Get formatted full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or ""


class SoftDeleteMixin:
    """Mixin adding soft delete functionality."""

    deleted_at: Mapped[dt.datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as soft deleted."""
        self.deleted_at = dt.datetime.now(dt.timezone.utc)
        # Only set is_enabled if it exists
        if hasattr(self, "is_enabled"):
            self.is_enabled = False

    def restore(self) -> None:
        """Restore soft deleted record."""
        self.deleted_at = None
        # Only set is_enabled if it exists
        if hasattr(self, "is_enabled"):
            self.is_enabled = True
