"""User Blueprint with authentication endpoints."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from flask_jwt_extended import create_access_token

from ..crud.crud_blueprint import CRUDMethod, MethodConfigMapping
from ..error import UnauthorizedError

if TYPE_CHECKING:
    from marshmallow import Schema

    from ..sqla.base_model import BaseModel
    from .user_models import User


def _get_perms_crud_blueprint() -> type:
    """Get the CRUDBlueprint class from perms module (includes mixins)."""
    from . import PermsBlueprint

    return PermsBlueprint


class UserBlueprint(_get_perms_crud_blueprint()):  # type: ignore[misc]
    """Blueprint for User CRUD operations with authentication endpoints.

    This blueprint extends CRUDBlueprint to provide:
    - Standard CRUD operations for User model (GET, POST, PATCH, DELETE)
    - Public login endpoint (POST /login/)
    - Current user profile endpoint (GET /me/)

    The login endpoint allows public registration if User.PUBLIC_REGISTRATION is True.

    Args:
        name: Blueprint name (default: "users")
        import_name: Import name (default: __name__)
        model: Model class or string (default: User)
        schema: Schema class or string (default: UserSchema)
        url_prefix: URL prefix for all routes (default: "/api/users/")
        methods: CRUD methods to enable (default: all methods)
        skip_methods: CRUD methods to disable (default: None)
        **kwargs: Additional arguments passed to CRUDBlueprint

    Example:
        >>> user_bp = UserBlueprint()
        >>> app.register_blueprint(user_bp)

        >>> # With custom configuration
        >>> user_bp = UserBlueprint(
        ...     url_prefix="/api/v2/users/",
        ...     skip_methods=[CRUDMethod.DELETE]
        ... )
    """

    def __init__(
        self,
        name: str = "users",
        import_name: str = __name__,
        model: type[BaseModel] | str | None = None,
        schema: type[Schema] | str | None = None,
        url_prefix: str | None = "/api/users/",
        methods: list[CRUDMethod] | MethodConfigMapping | None = None,
        skip_methods: list[CRUDMethod] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize UserBlueprint with default User model and schema."""
        # Set defaults for model and schema
        if model is None:
            from .user_models import User

            model = User

        if schema is None:
            from .user_schemas import UserSchema

            schema = UserSchema

        # Use default methods if not specified
        if methods is None:
            methods = list(CRUDMethod)

        super().__init__(
            name=name,
            import_name=import_name,
            model=model,
            schema=schema,
            url_prefix=url_prefix,
            methods=methods,
            skip_methods=skip_methods,
            **kwargs,
        )

        # Register additional user-specific endpoints
        self._register_login_endpoint()
        self._register_current_user_endpoint()

    def _register_login_endpoint(self) -> None:
        """Register the login endpoint."""
        from .user_models import User as UserModel
        from .user_schemas import TokenSchema, UserLoginSchema

        @self.public_endpoint
        @self.route("/login/", methods=["POST"])
        @self.arguments(UserLoginSchema)
        @self.response(HTTPStatus.OK, TokenSchema)
        def login(data: dict) -> dict[str, str]:
            """Login and get JWT token (public endpoint)."""

            user_model_cls: type[BaseModel] = self._config.model_cls

            # Make sure user_model_cls is a subclass of User
            if not issubclass(user_model_cls, UserModel):
                raise UnauthorizedError("Invalid user model for login")

            # Use bypass_perms since this is a public endpoint without auth
            with user_model_cls.bypass_perms():
                user = user_model_cls.get_by(email=data["email"])

            if not user or not user.is_password_correct(data["password"]):
                raise UnauthorizedError("Invalid email or password")

            if not user.is_enabled:
                raise UnauthorizedError("Account is disabled")

            access_token = create_access_token(identity=user.id)

            return {"access_token": access_token, "token_type": "bearer"}

    def _register_current_user_endpoint(self) -> None:
        """Register the current user profile endpoint."""

        user_schema_cls: type[Schema] = self._config.schema_cls

        @self.route("/me/", methods=["GET"])
        @self.response(HTTPStatus.OK, user_schema_cls)
        def get_current_user_profile() -> User:
            """Get current authenticated user's profile."""
            from .user_models import current_user

            if not current_user or not current_user.id:
                raise UnauthorizedError("Not authenticated")

            return current_user


# Create default instance for backward compatibility
user_bp = UserBlueprint()
