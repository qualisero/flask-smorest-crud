"""Tests for SQLAlchemy performance monitoring hooks."""

from __future__ import annotations

import logging
from collections.abc import Generator
from unittest.mock import patch

import pytest
from flask import Flask

from flask_more_smorest import db, init_db
from flask_more_smorest.sqla.database import get_request_query_stats


@pytest.fixture
def app_with_monitoring() -> Generator[Flask, None, None]:
    """Create a Flask app with performance monitoring enabled."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_PERFORMANCE_MONITORING"] = True
    app.config["SQLALCHEMY_SLOW_QUERY_THRESHOLD"] = 0.001  # Very low for testing

    init_db(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app_without_monitoring() -> Generator[Flask, None, None]:
    """Create a Flask app without performance monitoring."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    # Performance monitoring is off by default

    init_db(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_performance_monitoring_logs_slow_queries(app_with_monitoring: Flask, caplog: pytest.LogCaptureFixture) -> None:
    """Test that slow queries are logged when they exceed threshold."""
    import time
    from unittest.mock import patch

    import sqlalchemy as sa

    # Patch time.perf_counter to simulate a slow query
    original_perf_counter = time.perf_counter
    call_count = [0]

    def mock_perf_counter() -> float:
        call_count[0] += 1
        if call_count[0] % 2 == 0:
            # Second call (after query): return 10 seconds later
            return original_perf_counter() + 10.0
        return original_perf_counter()

    with patch("time.perf_counter", side_effect=mock_perf_counter):
        with caplog.at_level(logging.WARNING):
            db.session.execute(sa.text("SELECT 1"))

    # Check that slow query was logged
    assert any("Slow query detected" in record.message for record in caplog.records)


def test_performance_monitoring_tracks_request_stats(app_with_monitoring: Flask) -> None:
    """Test that query statistics are tracked per request."""
    import sqlalchemy as sa

    # Execute some queries
    db.session.execute(sa.text("SELECT 1"))
    db.session.execute(sa.text("SELECT 2"))
    db.session.execute(sa.text("SELECT 3"))

    stats = get_request_query_stats()

    assert stats["query_count"] >= 3
    assert stats["total_query_time"] > 0


def test_get_request_query_stats_without_context() -> None:
    """Test that get_request_query_stats returns zeros outside request context."""
    # Outside app context
    stats = get_request_query_stats()

    assert stats["query_count"] == 0
    assert stats["total_query_time"] == 0.0


def test_performance_monitoring_disabled_by_default(
    app_without_monitoring: Flask, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that performance monitoring is disabled by default."""
    import sqlalchemy as sa

    with caplog.at_level(logging.DEBUG):
        db.session.execute(sa.text("SELECT 1"))

    # No slow query log (monitoring disabled)
    assert not any("Slow query detected" in record.message for record in caplog.records)


def test_performance_monitoring_logs_info_on_enable(caplog: pytest.LogCaptureFixture) -> None:
    """Test that enabling monitoring logs an info message."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_PERFORMANCE_MONITORING"] = True

    with caplog.at_level(logging.INFO):
        init_db(app)

    assert any("performance monitoring enabled" in record.message for record in caplog.records)


def test_query_count_accumulates_within_request(app_with_monitoring: Flask) -> None:
    """Test that query counts accumulate within a request."""
    import sqlalchemy as sa

    # Get initial count
    initial_stats = get_request_query_stats()
    initial_count = initial_stats["query_count"]

    # Execute queries
    db.session.execute(sa.text("SELECT 1"))
    db.session.execute(sa.text("SELECT 2"))

    # Check counts increased
    final_stats = get_request_query_stats()
    assert final_stats["query_count"] >= initial_count + 2
    assert final_stats["total_query_time"] > 0


def test_slow_query_threshold_configurable() -> None:
    """Test that slow query threshold can be configured."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_PERFORMANCE_MONITORING"] = True
    app.config["SQLALCHEMY_SLOW_QUERY_THRESHOLD"] = 5.0  # 5 seconds

    init_db(app)

    with app.app_context():
        db.create_all()

        import sqlalchemy as sa

        # With a 5 second threshold, normal queries won't be logged as slow
        with patch.object(logging.getLogger("flask_more_smorest.sqla.database"), "warning") as mock_warning:
            db.session.execute(sa.text("SELECT 1"))
            # Should not be called since query is faster than 5s
            mock_warning.assert_not_called()

        db.session.remove()
        db.drop_all()
