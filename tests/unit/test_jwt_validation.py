"""Tests for JWT initialization and validation."""

from __future__ import annotations

import pytest
from flask import Flask

from flask_more_smorest import db, init_db
from flask_more_smorest.perms.jwt import init_jwt


def test_jwt_init_requires_secret_in_production() -> None:
    """Test that JWT_SECRET_KEY is required when not in debug/testing mode."""
    app = Flask(__name__)
    app.config["TESTING"] = False
    app.config["DEBUG"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    # Intentionally not setting JWT_SECRET_KEY

    init_db(app)

    with app.app_context():
        with pytest.raises(RuntimeError) as exc_info:
            init_jwt(app)

        assert "JWT_SECRET_KEY is required in production" in str(exc_info.value)
        assert "secrets.token_hex" in str(exc_info.value)

    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_jwt_init_warns_in_debug_mode(caplog: pytest.LogCaptureFixture) -> None:
    """Test that missing JWT_SECRET_KEY logs warning in debug mode."""
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["TESTING"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    # Intentionally not setting JWT_SECRET_KEY

    init_db(app)

    with app.app_context():
        init_jwt(app)

        # Should have logged a warning
        assert any("JWT_SECRET_KEY is not set" in record.message for record in caplog.records)

    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_jwt_init_warns_in_testing_mode(caplog: pytest.LogCaptureFixture) -> None:
    """Test that missing JWT_SECRET_KEY logs warning in testing mode."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["DEBUG"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    # Intentionally not setting JWT_SECRET_KEY

    init_db(app)

    with app.app_context():
        init_jwt(app)

        # Should have logged a warning
        assert any("JWT_SECRET_KEY is not set" in record.message for record in caplog.records)

    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_jwt_init_succeeds_with_secret_in_production() -> None:
    """Test that JWT initializes successfully with a secret key."""
    app = Flask(__name__)
    app.config["TESTING"] = False
    app.config["DEBUG"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "super-secret-key-for-production"

    init_db(app)

    with app.app_context():
        # Should not raise
        init_jwt(app)

    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_jwt_init_no_warning_with_secret(caplog: pytest.LogCaptureFixture) -> None:
    """Test that no warning is logged when JWT_SECRET_KEY is set."""
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "my-secret-key"

    init_db(app)

    with app.app_context():
        init_jwt(app)

        # Should NOT have logged a warning about missing key
        assert not any("JWT_SECRET_KEY is not set" in record.message for record in caplog.records)

    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()
