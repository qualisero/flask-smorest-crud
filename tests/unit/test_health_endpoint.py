"""Tests for the health check endpoint."""

from __future__ import annotations

import pytest
from flask import Flask

from flask_more_smorest import __version__, db, init_db
from flask_more_smorest.perms import Api


@pytest.fixture
def app_with_health() -> Flask:
    """Create a Flask app with Api initialized (includes health endpoint)."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["API_TITLE"] = "Test API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"

    init_db(app)
    Api(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_health_endpoint_returns_healthy(app_with_health: Flask) -> None:
    """Test that health endpoint returns healthy status."""
    with app_with_health.test_client() as client:
        response = client.get("/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["version"] == __version__
        assert "timestamp" in data


def test_health_endpoint_is_public(app_with_health: Flask) -> None:
    """Test that health endpoint doesn't require authentication."""
    with app_with_health.test_client() as client:
        # No auth headers provided
        response = client.get("/health")

        # Should still work without auth
        assert response.status_code == 200
        assert response.get_json()["status"] == "healthy"


def test_health_endpoint_custom_path() -> None:
    """Test that health endpoint path can be customized."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["API_TITLE"] = "Test API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["HEALTH_ENDPOINT_PATH"] = "/api/health"

    init_db(app)
    Api(app)

    with app.app_context():
        db.create_all()

        with app.test_client() as client:
            # Default path should not exist
            response = client.get("/health")
            assert response.status_code == 404

            # Custom path should work
            response = client.get("/api/health")
            assert response.status_code == 200
            assert response.get_json()["status"] == "healthy"

        db.session.remove()
        db.drop_all()


def test_health_endpoint_can_be_disabled() -> None:
    """Test that health endpoint can be disabled."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["API_TITLE"] = "Test API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["HEALTH_ENDPOINT_ENABLED"] = False

    init_db(app)
    Api(app)

    with app.app_context():
        db.create_all()

        with app.test_client() as client:
            response = client.get("/health")
            # Should return 404 since endpoint is disabled
            assert response.status_code == 404

        db.session.remove()
        db.drop_all()
