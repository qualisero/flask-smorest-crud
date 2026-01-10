"""Tests for RFC 7807 Problem Details error responses."""

from __future__ import annotations

from http import HTTPStatus

from flask import Flask

from flask_more_smorest.error.exceptions import (
    ApiException,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    UnprocessableEntity,
    _get_error_type_uri,
)


class CustomError(ApiException):
    """Custom error for testing."""

    TITLE = "Custom Error"
    HTTP_STATUS_CODE = HTTPStatus.BAD_REQUEST


def test_rfc7807_basic_structure() -> None:
    """Test that error response follows RFC 7807 structure."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        with app.test_request_context("/api/users/123"):
            error = NotFoundError("User not found")
            response = error.make_error_response()

    data = response.get_json()

    # Required RFC 7807 fields
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data

    # Values should be correct
    assert data["title"] == "Not Found"
    assert data["status"] == 404
    assert data["detail"] == "User not found"
    assert data["instance"] == "/api/users/123"


def test_rfc7807_content_type() -> None:
    """Test that response has correct content type."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        error = NotFoundError("Resource not found")
        response = error.make_error_response()

    assert response.content_type == "application/problem+json"


def test_rfc7807_type_uri() -> None:
    """Test that type URI is correctly generated."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        uri = _get_error_type_uri("not_found_error")
        assert uri == "/errors/not_found_error"


def test_rfc7807_custom_type_base_url() -> None:
    """Test that type URI base can be customized."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["ERROR_TYPE_BASE_URL"] = "https://api.example.com/errors"

    with app.app_context():
        uri = _get_error_type_uri("not_found_error")
        assert uri == "https://api.example.com/errors/not_found_error"


def test_rfc7807_includes_fields_if_provided() -> None:
    """Test that custom fields are included in response."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        error = BadRequestError("Invalid input", field="email", reason="invalid format")
        response = error.make_error_response()

    data = response.get_json()
    assert "fields" in data
    assert data["fields"]["field"] == "email"
    assert data["fields"]["reason"] == "invalid format"


def test_rfc7807_debug_info_in_testing_mode() -> None:
    """Test that debug info is included in testing mode."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        try:
            raise NotFoundError("Not found")
        except NotFoundError as error:
            response = error.make_error_response()

    data = response.get_json()
    assert "debug" in data
    assert "error_code" in data["debug"]


def test_rfc7807_no_debug_info_in_production() -> None:
    """Test that debug info is NOT included in production mode."""
    app = Flask(__name__)
    app.config["TESTING"] = False
    app.config["DEBUG"] = False

    with app.app_context():
        error = NotFoundError("Not found")
        response = error.make_error_response()

    data = response.get_json()
    assert "debug" not in data


def test_rfc7807_validation_error_format() -> None:
    """Test that UnprocessableEntity includes validation errors."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        error = UnprocessableEntity(
            fields={"email": "Invalid email format", "age": "Must be positive"},
            location="json",
            message="Validation failed",
        )
        response = error.make_error_response()

    data = response.get_json()

    assert data["title"] == "Validation Error"
    assert data["status"] == 422
    assert data["detail"] == "Validation failed"
    assert "errors" in data
    assert "json" in data["errors"]
    assert "email" in data["errors"]["json"]
    assert "age" in data["errors"]["json"]


def test_unauthorized_error_no_traceback() -> None:
    """Test that UnauthorizedError never includes traceback."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        try:
            raise UnauthorizedError("Invalid token")
        except UnauthorizedError as error:
            response = error.make_error_response()

    data = response.get_json()
    # Even with debug info, traceback should not be included
    if "debug" in data:
        assert "traceback" not in data["debug"]


def test_instance_field_only_in_request_context() -> None:
    """Test that instance field is only included in request context."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        # Outside request context
        error = NotFoundError("Not found")
        response = error.make_error_response()
        data = response.get_json()
        assert "instance" not in data

        # Inside request context
        with app.test_request_context("/api/test"):
            error = NotFoundError("Not found")
            response = error.make_error_response()
            data = response.get_json()
            assert data["instance"] == "/api/test"


def test_error_titles_are_human_readable() -> None:
    """Test that all error types have human-readable titles."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        assert NotFoundError.TITLE == "Not Found"
        assert ForbiddenError.TITLE == "Forbidden"
        assert UnauthorizedError.TITLE == "Unauthorized"
        assert BadRequestError.TITLE == "Bad Request"
        assert UnprocessableEntity.TITLE == "Validation Error"
