"""Unit tests for UserBlueprint class."""

# pyright: reportAttributeAccessIssue=false

from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest
from flask import Flask

from flask_more_smorest import Api, User, UserBlueprint, db, init_db, init_jwt
from flask_more_smorest.crud.crud_blueprint import CRUDMethod
from flask_more_smorest.error.error_handlers import RequestHandlers

if TYPE_CHECKING:
    from sqlalchemy.orm import scoped_session


@pytest.fixture(scope="function")
def test_app() -> Flask:
    """Create a Flask app for testing UserBlueprint."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False  # Allow error handlers to work
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["API_TITLE"] = "UserBlueprint Test API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["JWT_SECRET_KEY"] = "jwt-test-secret-key"

    init_db(app)
    init_jwt(app)
    RequestHandlers(app)  # Register error handlers

    return app


@pytest.fixture(scope="function")
def db_session(test_app: Flask) -> Iterator["scoped_session"]:
    """Create a database session for tests."""
    with test_app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def api(test_app: Flask, db_session: "scoped_session") -> Api:
    """Create API instance."""
    return Api(test_app)


class TestUserBlueprintClass:
    """Tests for UserBlueprint class."""

    def test_user_blueprint_instantiation_with_defaults(self, test_app: Flask, api: Api) -> None:
        """Test UserBlueprint can be instantiated with default parameters."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        assert bp.name == "users"
        assert bp.url_prefix == "/api/users/"

    def test_user_blueprint_custom_configuration(self, test_app: Flask, api: Api) -> None:
        """Test UserBlueprint can be instantiated with custom parameters."""
        bp = UserBlueprint(
            name="custom_users",
            url_prefix="/api/v2/users/",
            skip_methods=[CRUDMethod.DELETE],
        )
        api.register_blueprint(bp)

        assert bp.name == "custom_users"
        assert bp.url_prefix == "/api/v2/users/"

    def test_user_blueprint_has_crud_endpoints(self, test_app: Flask, api: Api, db_session: "scoped_session") -> None:
        """Test UserBlueprint registers standard CRUD endpoints."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        # Check that CRUD routes are registered
        with test_app.app_context():
            rules = [rule.rule for rule in test_app.url_map.iter_rules()]

            # Standard CRUD routes
            assert "/api/users/" in rules  # INDEX and POST
            assert "/api/users/<uuid:users_id>" in rules  # GET, PATCH, DELETE

    def test_user_blueprint_has_login_endpoint(self, test_app: Flask, api: Api, db_session: "scoped_session") -> None:
        """Test UserBlueprint registers login endpoint."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        # Check login route is registered
        with test_app.app_context():
            rules = [rule.rule for rule in test_app.url_map.iter_rules()]
            assert "/api/users/login/" in rules

    def test_user_blueprint_has_me_endpoint(self, test_app: Flask, api: Api, db_session: "scoped_session") -> None:
        """Test UserBlueprint registers current user profile endpoint."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        # Check /me route is registered
        with test_app.app_context():
            rules = [rule.rule for rule in test_app.url_map.iter_rules()]
            assert "/api/users/me/" in rules

    def test_user_blueprint_login_endpoint_works(self, test_app: Flask, api: Api, db_session: "scoped_session") -> None:
        """Test login endpoint returns JWT token."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        client = test_app.test_client()

        # Create a test user
        with User.bypass_perms():
            user = User(email="test@example.com", password="password123")
            user.save()

        # Login
        response = client.post(
            "/api/users/login/",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_user_blueprint_login_fails_with_wrong_password(
        self, test_app: Flask, api: Api, db_session: "scoped_session"
    ) -> None:
        """Test login endpoint rejects wrong password."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        client = test_app.test_client()

        # Create a test user
        with User.bypass_perms():
            user = User(email="test@example.com", password="password123")
            user.save()

        # Try to login with wrong password
        response = client.post(
            "/api/users/login/",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
        assert data["error"]["error_code"] == "unauthorized_error"

    def test_user_blueprint_login_fails_for_disabled_user(
        self, test_app: Flask, api: Api, db_session: "scoped_session"
    ) -> None:
        """Test login endpoint rejects disabled users."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        client = test_app.test_client()

        # Create a disabled test user
        with User.bypass_perms():
            user = User(email="test@example.com", password="password123", is_enabled=False)
            user.save()

        # Try to login
        response = client.post(
            "/api/users/login/",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
        assert "disabled" in data["error"]["debug"]["message"].lower()

    def test_user_blueprint_me_endpoint_requires_auth(
        self, test_app: Flask, api: Api, db_session: "scoped_session"
    ) -> None:
        """Test /me endpoint requires authentication."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        client = test_app.test_client()

        # Try to access /me without authentication
        response = client.get("/api/users/me/")
        assert response.status_code == 401

    def test_user_blueprint_me_endpoint_returns_current_user(
        self, test_app: Flask, api: Api, db_session: "scoped_session"
    ) -> None:
        """Test /me endpoint returns current authenticated user."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        client = test_app.test_client()

        # Create a test user and login
        with User.bypass_perms():
            user = User(email="test@example.com", password="password123")
            user.save()

        # Login to get token
        login_response = client.post(
            "/api/users/login/",
            json={"email": "test@example.com", "password": "password123"},
        )
        token = login_response.get_json()["access_token"]

        # Access /me endpoint
        response = client.get(
            "/api/users/me/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "password" not in data  # Password should be excluded

    def test_user_blueprint_skip_methods(self, test_app: Flask, api: Api, db_session: "scoped_session") -> None:
        """Test UserBlueprint respects skip_methods parameter."""
        bp = UserBlueprint(skip_methods=[CRUDMethod.DELETE])
        api.register_blueprint(bp)

        # Check that DELETE route is not registered
        with test_app.app_context():
            # Get all routes and their methods
            delete_routes = [
                rule
                for rule in test_app.url_map.iter_rules()
                if "/api/users/<users_id>" in rule.rule and rule.methods is not None and "DELETE" in rule.methods
            ]
            assert len(delete_routes) == 0

    def test_user_blueprint_inherits_from_crud_blueprint(self) -> None:
        """Test that UserBlueprint inherits from PermsBlueprint (CRUDBlueprint with mixins)."""
        from flask_more_smorest.perms import PermsBlueprint

        assert issubclass(UserBlueprint, PermsBlueprint)

    def test_user_blueprint_has_permission_decorators(self, test_app: Flask, api: Api) -> None:
        """Test that UserBlueprint has permission-related decorators."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        # Check that UserBlueprint has permission decorators
        assert hasattr(bp, "public_endpoint")
        assert callable(bp.public_endpoint)


class TestUserBlueprintWithCustomUser:
    """Test UserBlueprint with custom User model."""

    def test_user_blueprint_with_custom_user_class(
        self, test_app: Flask, api: Api, db_session: "scoped_session"
    ) -> None:
        """Test UserBlueprint works with custom User model."""

        # Define a custom User class with PUBLIC_REGISTRATION
        class CustomUser(User):
            PUBLIC_REGISTRATION = True

        # Create blueprint with custom user model
        bp = UserBlueprint(model=CustomUser, schema=CustomUser.Schema)
        api.register_blueprint(bp)

        # Verify the blueprint uses the custom model
        assert bp._config.model_cls == CustomUser

        # Verify PUBLIC_REGISTRATION flag is set
        assert CustomUser.PUBLIC_REGISTRATION is True


class TestUserBlueprintIntegration:
    """Integration tests for UserBlueprint with full app setup."""

    def test_complete_user_registration_and_login_flow(
        self, test_app: Flask, api: Api, db_session: "scoped_session"
    ) -> None:
        """Test complete user flow: create -> login -> access profile -> update."""
        bp = UserBlueprint()
        api.register_blueprint(bp)

        client = test_app.test_client()

        # Step 1: Create a new user (bypassing perms for test)
        with User.bypass_perms():
            user = User(email="newuser@example.com", password="securepass123")
            user.save()
            user_id = user.id

        # Step 2: Login with the new user
        login_response = client.post(
            "/api/users/login/",
            json={"email": "newuser@example.com", "password": "securepass123"},
        )
        assert login_response.status_code == 200
        token_data = login_response.get_json()
        token = token_data["access_token"]

        # Step 3: Access profile using /me endpoint
        profile_response = client.get(
            "/api/users/me/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_response.status_code == 200
        profile_data = profile_response.get_json()
        assert profile_data["email"] == "newuser@example.com"
        assert profile_data["id"] == str(user_id)

        # Step 4: Get user details
        get_response = client.get(
            f"/api/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        get_data = get_response.get_json()
        assert get_data["email"] == "newuser@example.com"

    def test_multiple_user_blueprints(self, test_app: Flask, api: Api, db_session: "scoped_session") -> None:
        """Test that multiple UserBlueprints can coexist with different configs."""

        # Create two UserBlueprints with different prefixes
        bp1 = UserBlueprint(name="users_v1", url_prefix="/api/v1/users/")
        bp2 = UserBlueprint(name="users_v2", url_prefix="/api/v2/users/")

        api.register_blueprint(bp1)
        api.register_blueprint(bp2)

        client = test_app.test_client()

        # Create a user via v1
        with User.bypass_perms():
            user = User(email="test@example.com", password="password123")
            user.save()

        # Login via v1
        v1_login = client.post(
            "/api/v1/users/login/",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert v1_login.status_code == 200

        # Login via v2
        v2_login = client.post(
            "/api/v2/users/login/",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert v2_login.status_code == 200

        # Both should work
        assert v1_login.get_json()["access_token"]
        assert v2_login.get_json()["access_token"]


class TestBackwardCompatibility:
    """Test backward compatibility with user_bp instance."""

    def test_user_bp_instance_exists(self) -> None:
        """Test that user_bp instance is available for backward compatibility."""
        from flask_more_smorest.perms import user_bp

        assert user_bp is not None
        assert isinstance(user_bp, UserBlueprint)
        assert user_bp.name == "users"

    def test_user_bp_instance_works(self, test_app: Flask, api: Api, db_session: "scoped_session") -> None:
        """Test that user_bp instance can be used directly."""
        from flask_more_smorest.perms import user_bp

        api.register_blueprint(user_bp)

        client = test_app.test_client()

        # Create a test user
        with User.bypass_perms():
            user = User(email="test@example.com", password="password123")
            user.save()

        # Login using user_bp
        response = client.post(
            "/api/users/login/",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        assert "access_token" in response.get_json()
