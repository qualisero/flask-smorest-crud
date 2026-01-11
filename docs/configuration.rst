Configuration
=============

Flask-More-Smorest extends Flask's configuration system with additional options for health checks, performance monitoring, error handling, and more.

Core Configuration
------------------

Required Settings
~~~~~~~~~~~~~~~~~

.. code-block:: python

   app.config.update(
       # Flask-Smorest API configuration
       API_TITLE="My API",
       API_VERSION="v1",
       OPENAPI_VERSION="3.0.2",
       
       # Database
       SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
       
       # Security (REQUIRED in production)
       SECRET_KEY="your-secret-key",
       JWT_SECRET_KEY="your-jwt-secret-key",
   )

.. warning::
   As of version 0.6.0, ``JWT_SECRET_KEY`` is **required** in production mode.
   Production is detected when both ``app.debug`` and ``app.testing`` are ``False``.
   The application will raise a ``RuntimeError`` at startup if this is not set.

Health Check Endpoint
---------------------

Flask-More-Smorest provides a built-in health check endpoint for load balancers and monitoring systems.

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Option
     - Default
     - Description
   * - ``HEALTH_ENDPOINT_ENABLED``
     - ``True``
     - Enable or disable the health check endpoint
   * - ``HEALTH_ENDPOINT_PATH``
     - ``"/health"``
     - URL path for the health check endpoint

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   app.config.update(
       HEALTH_ENDPOINT_ENABLED=True,
       HEALTH_ENDPOINT_PATH="/api/health",
   )

Health Check Response
~~~~~~~~~~~~~~~~~~~~~

The health endpoint returns JSON with application status:

.. code-block:: json

   {
     "status": "healthy",
     "timestamp": "2026-01-11T08:30:00+00:00",
     "version": "0.6.0",
     "database": "connected"
   }

**Status Codes:**

- ``200 OK``: Application is healthy and database is connected
- ``503 Service Unavailable``: Database connection failed

The endpoint is automatically marked as public (no authentication required).

Performance Monitoring
----------------------

SQLAlchemy performance monitoring helps identify slow queries and track database performance.

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Option
     - Default
     - Description
   * - ``SQLALCHEMY_PERFORMANCE_MONITORING``
     - ``False``
     - Enable performance monitoring
   * - ``SQLALCHEMY_SLOW_QUERY_THRESHOLD``
     - ``1.0``
     - Log queries slower than this (seconds)
   * - ``SQLALCHEMY_LOG_ALL_QUERIES``
     - ``False``
     - Log all queries at DEBUG level
   * - ``SQLALCHEMY_LOG_QUERY_PARAMETERS``
     - ``True``
     - Include query parameters in logs

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   app.config.update(
       SQLALCHEMY_PERFORMANCE_MONITORING=True,
       SQLALCHEMY_SLOW_QUERY_THRESHOLD=0.5,  # Log queries over 500ms
       SQLALCHEMY_LOG_ALL_QUERIES=False,     # Only log slow queries
   )

Slow Query Logging
~~~~~~~~~~~~~~~~~~

When a query exceeds the threshold, it's logged at WARNING level:

.. code-block:: text

   WARNING flask_more_smorest.sqla.database: Slow query detected: 2.345s - SELECT * FROM large_table WHERE ...

Request Statistics
~~~~~~~~~~~~~~~~~~

Track query count and total time per request:

.. code-block:: python

   from flask_more_smorest.sqla import get_request_query_stats

   @app.after_request
   def log_query_stats(response):
       stats = get_request_query_stats()
       if stats['query_count'] > 10:
           app.logger.warning(
               f"High query count: {stats['query_count']} queries, "
               f"total time: {stats['total_query_time']:.3f}s"
           )
       return response

.. note::
   Performance monitoring has minimal overhead when disabled (no event listeners registered).
   Query text is truncated in logs to avoid overwhelming log storage.

Error Handling
--------------

RFC 7807 Problem Details
~~~~~~~~~~~~~~~~~~~~~~~~~

As of version 0.6.0, all error responses follow the `RFC 7807 Problem Details <https://datatracker.ietf.org/doc/html/rfc7807>`_ standard.

Configuration Options
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Option
     - Default
     - Description
   * - ``ERROR_TYPE_BASE_URL``
     - ``"/errors"``
     - Base URL for error type URIs

Error Response Format
^^^^^^^^^^^^^^^^^^^^^

**Production mode** (``app.debug=False`` and ``app.testing=False``):

.. code-block:: json

   {
     "type": "/errors/not_found_error",
     "title": "Not Found",
     "status": 404,
     "detail": "User with id 123 doesn't exist",
     "instance": "/api/users/123"
   }

**Debug/Testing mode** includes additional debug information:

.. code-block:: json

   {
     "type": "/errors/forbidden_error",
     "title": "Forbidden",
     "status": 403,
     "detail": "User not allowed to modify this resource",
     "instance": "/api/resources/456",
     "debug": {
       "error_code": "forbidden_error",
       "context": {"user_id": "...", "resource_id": "..."},
       "traceback": ["...", "..."]
     }
   }

Content-Type
^^^^^^^^^^^^

All error responses use ``Content-Type: application/problem+json``.

.. warning::
   **Breaking Change in 0.6.0**: The error response format changed from a custom format
   to RFC 7807. Update your client error handling accordingly.

   **Before (0.5.x)**:
   
   .. code-block:: json
   
      {"error": {"status_code": 404, "title": "Not Found", "error_code": "not_found_error"}}
   
   **After (0.6.0+)**:
   
   .. code-block:: json
   
      {"type": "/errors/not_found_error", "title": "Not Found", "status": 404, "detail": "..."}

Security Configuration
----------------------

Debug Information Exposure
~~~~~~~~~~~~~~~~~~~~~~~~~~

Debug information (tracebacks, context) is automatically controlled by Flask's environment:

- **Production** (``app.debug=False`` and ``app.testing=False``): No debug info in error responses
- **Debug/Testing**: Full debug information included in ``debug`` field

This is handled automatically and requires no configuration.

JWT Secret Validation
~~~~~~~~~~~~~~~~~~~~~~

The JWT secret key is validated at startup:

- **Production**: ``RuntimeError`` raised if ``JWT_SECRET_KEY`` is not set
- **Development/Testing**: Warning logged if ``JWT_SECRET_KEY`` is missing

Generate a secure key:

.. code-block:: bash

   python -c "import secrets; print(secrets.token_urlsafe(32))"

Pagination
----------

Control default pagination behavior:

.. code-block:: python

   app.config.update(
       DEFAULT_PAGE_SIZE=20,      # Default items per page
       MAX_PAGE_SIZE=100,         # Maximum allowed page size
   )

Full Example
------------

Here's a complete configuration for a production application:

.. code-block:: python

   import os
   from flask import Flask
   from flask_more_smorest import init_db
   from flask_more_smorest.perms import Api

   app = Flask(__name__)
   app.config.update(
       # Flask-Smorest API
       API_TITLE="My Production API",
       API_VERSION="v1",
       OPENAPI_VERSION="3.0.2",
       
       # Database
       SQLALCHEMY_DATABASE_URI=os.environ["DATABASE_URL"],
       
       # Security
       SECRET_KEY=os.environ["SECRET_KEY"],
       JWT_SECRET_KEY=os.environ["JWT_SECRET_KEY"],
       
       # Health Check
       HEALTH_ENDPOINT_ENABLED=True,
       HEALTH_ENDPOINT_PATH="/health",
       
       # Performance Monitoring (enable in staging/dev)
       SQLALCHEMY_PERFORMANCE_MONITORING=os.environ.get("ENABLE_PERF_MONITORING", "false").lower() == "true",
       SQLALCHEMY_SLOW_QUERY_THRESHOLD=0.5,
       
       # Error Handling
       ERROR_TYPE_BASE_URL="/api/errors",
       
       # Pagination
       DEFAULT_PAGE_SIZE=20,
       MAX_PAGE_SIZE=100,
   )

   init_db(app)
   api = Api(app)
