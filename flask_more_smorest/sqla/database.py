"""Database configuration and utilities for flask-more-smorest.

This module provides the core SQLAlchemy setup and utilities for
configuring custom User models and other database-related functionality.
"""

import logging
import time
from typing import TYPE_CHECKING, Any

from flask import g, has_app_context
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from flask import Flask
    from sqlalchemy.engine.interfaces import DBAPICursor, ExecutionContext

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    This serves as the declarative base for all models in the application.
    It provides the foundation for SQLAlchemy's ORM functionality.
    """

    pass


# Main database instance
db: SQLAlchemy = SQLAlchemy(model_class=Base)


def init_db(app: "Flask") -> None:
    """Initialize the database with the Flask application.

    This function binds the SQLAlchemy database instance to the Flask
    application, making it available throughout the application context.

    Args:
        app: Flask application instance to initialize the database with

    Example:
        >>> from flask import Flask
        >>> from flask_more_smorest.sqla import init_db
        >>>
        >>> app = Flask(__name__)
        >>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
        >>> init_db(app)
    """
    db.init_app(app)

    # Register performance monitoring if enabled
    if app.config.get("SQLALCHEMY_PERFORMANCE_MONITORING", False):
        _register_performance_hooks(app)


def _register_performance_hooks(app: "Flask") -> None:
    """Register SQLAlchemy event hooks for performance monitoring.

    This sets up before/after cursor execute events to track query
    execution times and log slow queries.

    Args:
        app: Flask application for configuration
    """
    # Get configuration
    slow_query_threshold = app.config.get("SQLALCHEMY_SLOW_QUERY_THRESHOLD", 1.0)
    log_all_queries = app.config.get("SQLALCHEMY_LOG_ALL_QUERIES", False)

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(
        conn: Any,
        cursor: "DBAPICursor",
        statement: str,
        parameters: Any,
        context: "ExecutionContext | None",
        executemany: bool,
    ) -> None:
        """Record query start time before execution."""
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(
        conn: Any,
        cursor: "DBAPICursor",
        statement: str,
        parameters: Any,
        context: "ExecutionContext | None",
        executemany: bool,
    ) -> None:
        """Calculate query duration and log if slow."""
        start_times = conn.info.get("query_start_time", [])
        if not start_times:
            return

        duration = time.perf_counter() - start_times.pop(-1)

        # Track request-level statistics if in request context
        if has_app_context():
            if not hasattr(g, "query_count"):
                g.query_count = 0
                g.total_query_time = 0.0
            g.query_count += 1
            g.total_query_time += duration

        # Log slow queries
        if duration >= slow_query_threshold:
            # Truncate long queries for logging
            truncated_statement = statement[:500] + "..." if len(statement) > 500 else statement
            logger.warning(
                "Slow query detected: %.3fs - %s",
                duration,
                truncated_statement,
                extra={
                    "duration": duration,
                    "query": truncated_statement,
                    "parameters": str(parameters)[:200] if parameters else None,
                },
            )
        elif log_all_queries:
            logger.debug(
                "Query executed: %.3fs - %s",
                duration,
                statement[:200],
            )

    logger.info(
        "SQLAlchemy performance monitoring enabled (slow query threshold: %.2fs)",
        slow_query_threshold,
    )


def get_request_query_stats() -> dict[str, Any]:
    """Get query statistics for the current request.

    Returns a dictionary with query count and total time.
    Only available when SQLALCHEMY_PERFORMANCE_MONITORING is enabled.

    Returns:
        Dictionary with 'query_count' and 'total_query_time' keys

    Example:
        >>> stats = get_request_query_stats()
        >>> print(f"Queries: {stats['query_count']}, Time: {stats['total_query_time']:.3f}s")
    """
    if has_app_context():
        return {
            "query_count": getattr(g, "query_count", 0),
            "total_query_time": getattr(g, "total_query_time", 0.0),
        }
    return {"query_count": 0, "total_query_time": 0.0}
