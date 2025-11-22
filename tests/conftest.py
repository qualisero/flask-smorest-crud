"""Test configuration and fixtures for flask-smorest-crud tests."""

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_smorest import Api
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import Schema, fields
from datetime import datetime


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["API_TITLE"] = "Test API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["SECRET_KEY"] = "test-secret-key"

    return app


@pytest.fixture
def db(app):
    """Create and configure a test database."""
    db = SQLAlchemy(app)

    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()


@pytest.fixture
def api(app):
    """Create a test API instance."""
    return Api(app)


@pytest.fixture
def user_model(db):
    """Create a test User model."""

    class User(db.Model):
        __tablename__ = "users"

        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        is_active = db.Column(db.Boolean, default=True)
        age = db.Column(db.Integer, nullable=True)

        def __repr__(self):
            return f"<User {self.username}>"

    db.create_all()
    return User


@pytest.fixture
def user_schema(user_model):
    """Create a test User schema."""

    class UserSchema(SQLAlchemyAutoSchema):
        class Meta:
            model = user_model
            load_instance = True
            include_fk = True

    return UserSchema


@pytest.fixture
def sample_users(db, user_model):
    """Create sample user data for testing."""
    users = [
        user_model(username="alice", email="alice@example.com", age=25, is_active=True),
        user_model(username="bob", email="bob@example.com", age=30, is_active=False),
        user_model(username="charlie", email="charlie@example.com", age=35, is_active=True),
    ]

    for user in users:
        db.session.add(user)

    db.session.commit()
    return users


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner."""
    return app.test_cli_runner()


# Globals that need to be available to modules
globals()["User"] = None
globals()["UserSchema"] = None


def set_test_models(user_model, user_schema):
    """Set global test models for import by CRUD blueprint."""
    globals()["User"] = user_model
    globals()["UserSchema"] = user_schema
