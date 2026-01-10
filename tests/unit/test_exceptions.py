"""Regression tests for ApiException responses."""

from __future__ import annotations

from http import HTTPStatus

from flask import Flask

from flask_more_smorest.error.exceptions import (
    ApiException,
    ForbiddenError,
    UnauthorizedError,
    _is_debug_mode,
)


class DummyException(ApiException):
    HTTP_STATUS_CODE = HTTPStatus.BAD_REQUEST


class NoTracebackException(ApiException):
    HTTP_STATUS_CODE = HTTPStatus.INTERNAL_SERVER_ERROR
    INCLUDE_TRACEBACK = False


class ExplicitTracebackException(ApiException):
    HTTP_STATUS_CODE = HTTPStatus.INTERNAL_SERVER_ERROR
    INCLUDE_TRACEBACK = True


def test_is_debug_mode_outside_app_context() -> None:
    """Test that _is_debug_mode returns False without app context."""
    assert _is_debug_mode() is False


def test_is_debug_mode_in_debug_app() -> None:
    """Test that _is_debug_mode returns True in debug mode."""
    app = Flask(__name__)
    app.config["DEBUG"] = True
    with app.app_context():
        assert _is_debug_mode() is True


def test_is_debug_mode_in_testing_app() -> None:
    """Test that _is_debug_mode returns True in testing mode."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    with app.app_context():
        assert _is_debug_mode() is True


def test_is_debug_mode_in_production() -> None:
    """Test that _is_debug_mode returns False in production."""
    app = Flask(__name__)
    app.config["DEBUG"] = False
    app.config["TESTING"] = False
    with app.app_context():
        assert _is_debug_mode() is False


def test_api_exception_includes_debug_context_in_debug_mode() -> None:
    """Test that debug context is included when DEBUG=True."""
    app = Flask(__name__)
    app.config["DEBUG"] = True

    with app.app_context():
        try:
            raise DummyException("problem", extra="info")
        except DummyException as exc:
            response = exc.make_error_response()

    payload = response.get_json()["error"]
    assert payload["status_code"] == HTTPStatus.BAD_REQUEST
    assert payload["details"]["extra"] == "info"
    assert "debug" in payload
    assert payload["debug"]["debug_context"]["extra"] == "info"
    assert "traceback" in payload["debug"]["debug_context"]


def test_api_exception_excludes_debug_in_production() -> None:
    """Test that debug context is NOT included in production mode."""
    app = Flask(__name__)
    app.config["DEBUG"] = False
    app.config["TESTING"] = False

    with app.app_context():
        try:
            raise DummyException("problem", extra="info")
        except DummyException as exc:
            response = exc.make_error_response()

    payload = response.get_json()["error"]
    assert payload["status_code"] == HTTPStatus.BAD_REQUEST
    assert payload["details"]["extra"] == "info"
    # Debug should NOT be included in production
    assert "debug" not in payload


def test_api_exception_trims_traceback_when_disabled() -> None:
    """Test that traceback is excluded when INCLUDE_TRACEBACK=False."""
    app = Flask(__name__)
    app.config["DEBUG"] = True  # Even with debug on

    with app.app_context():
        try:
            raise NoTracebackException("fail")
        except NoTracebackException as exc:
            response = exc.make_error_response()

    payload = response.get_json()["error"]
    # Debug is included because we're in debug mode
    assert "debug" in payload
    # But traceback is explicitly disabled
    assert "traceback" not in payload["debug"]["debug_context"]


def test_api_exception_explicit_traceback_in_production() -> None:
    """Test that explicit INCLUDE_TRACEBACK=True still excludes debug in production."""
    app = Flask(__name__)
    app.config["DEBUG"] = False
    app.config["TESTING"] = False

    with app.app_context():
        try:
            raise ExplicitTracebackException("fail")
        except ExplicitTracebackException as exc:
            response = exc.make_error_response()

    payload = response.get_json()["error"]
    # Even with explicit traceback, debug block is not included in production
    assert "debug" not in payload


def test_subclass_without_extra_kwargs() -> None:
    """Test UnauthorizedError message handling."""
    app = Flask(__name__)
    app.config["DEBUG"] = True

    with app.app_context():
        response = UnauthorizedError("no token").make_error_response()

    payload = response.get_json()["error"]
    assert payload["debug"]["message"] == "no token"
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    # UnauthorizedError has INCLUDE_TRACEBACK=False explicitly
    assert "traceback" not in payload["debug"]["debug_context"]


def test_unauthorized_error_never_includes_traceback() -> None:
    """Test that UnauthorizedError never includes traceback for security."""
    app = Flask(__name__)
    app.config["DEBUG"] = True

    with app.app_context():
        try:
            raise UnauthorizedError("forbidden")
        except UnauthorizedError as exc:
            response = exc.make_error_response()

    payload = response.get_json()["error"]
    # UnauthorizedError explicitly sets INCLUDE_TRACEBACK=False
    # so even in debug mode, no traceback
    assert "traceback" not in payload["debug"]["debug_context"]


def test_forbidden_error_uses_environment_detection() -> None:
    """Test that ForbiddenError uses environment-aware traceback."""
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # ForbiddenError has INCLUDE_TRACEBACK=None (uses environment detection)
    assert ForbiddenError.INCLUDE_TRACEBACK is None
