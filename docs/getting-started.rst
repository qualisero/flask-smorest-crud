Getting Started
===============

Installation
------------

Install flask-more-smorest using pip:

.. code-block:: bash

   pip install flask-more-smorest

Quick Start
-----------

Here's a minimal example to get you started:

.. code-block:: python

   from flask import Flask
   from flask_more_smorest import init_db
   from flask_more_smorest.perms import Api, CRUDBlueprint

   # Create Flask app
   app = Flask(__name__)
   app.config.update(
       API_TITLE="My API",
       API_VERSION="v1",
       OPENAPI_VERSION="3.0.2",
       SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
       SECRET_KEY="change-me",
       JWT_SECRET_KEY="change-me-too",
   )

   # Initialize database
   init_db(app)

   # Create API instance with JWT and permission hooks
   api = Api(app)

   # Create a CRUD blueprint
   users = CRUDBlueprint(
       "users",
       __name__,
       model="User",        # resolved from your models module
       schema="UserSchema",  # resolved from your schemas module
       url_prefix="/api/users/",
   )

   # Register blueprint
   api.register_blueprint(users)

   if __name__ == "__main__":
       app.run(debug=True)

This automatically creates the following endpoints:

- ``GET /api/users/`` - List all users (with pagination and filtering)
- ``POST /api/users/`` - Create a new user
- ``GET /api/users/<id>`` - Get a specific user
- ``PATCH /api/users/<id>`` - Update a user
- ``DELETE /api/users/<id>`` - Delete a user

Creating Models
---------------

Use ``BaseModel`` to create models with automatic features:

.. code-block:: python

   from flask_more_smorest import BaseModel
   from flask_more_smorest.sqla import db
   from sqlalchemy.orm import Mapped, mapped_column

   class User(BaseModel):
       # __tablename__ is automatically set to "user" (snake_case of class name)
       # You can override it if needed: __tablename__ = "custom_users"

       username: Mapped[str] = mapped_column(db.String(80), unique=True, nullable=False)
       email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
       is_active: Mapped[bool] = mapped_column(db.Boolean, default=True)

``BaseModel`` automatically provides:

- UUID primary key (``id``)
- Timestamps (``created_at``, ``updated_at``)
- CRUD helper methods (``save()``, ``update()``, ``delete()``, ``get_by()``, ``get_by_or_404()``)
- Automatic Marshmallow schema generation (``User.Schema``)
- **Automatic table naming** (class name converted to snake_case)

.. note::
   
   The ``__tablename__`` attribute is **optional**. SQLAlchemy automatically generates 
   table names by converting your class name to snake_case. For example:
   
   - ``User`` → ``user``
   - ``UserProfile`` → ``user_profile``
   - ``ArticleComment`` → ``article_comment``
   
   Only specify ``__tablename__`` if you need a custom table name.

Controlling CRUD Endpoints
---------------------------

You can customize which endpoints are created:

.. code-block:: python

   from flask_more_smorest.crud.crud_blueprint import CRUDMethod

   # Enable only specific methods
   users = CRUDBlueprint(
       "users",
       __name__,
       model="User",
       schema="UserSchema",
       methods=[CRUDMethod.INDEX, CRUDMethod.GET],  # Only list and get
   )

   # Or customize specific methods
   users = CRUDBlueprint(
       "users",
       __name__,
       model="User",
       schema="UserSchema",
       methods={
           CRUDMethod.POST: {"schema": "UserWriteSchema"},  # Custom schema for POST
           CRUDMethod.DELETE: {"admin_only": True},         # Admin-only endpoint
           CRUDMethod.PATCH: False,                         # Disable PATCH
       },
   )

When using a dict for ``methods``, all methods are enabled by default unless explicitly disabled with ``False``.

Filtering and Pagination
-------------------------

CRUD endpoints automatically support filtering and pagination:

.. code-block:: bash

   # Filter by field values
   GET /api/users/?username=john&is_active=true

   # Date range filtering
   GET /api/users/?created_at__from=2024-01-01&created_at__to=2024-12-31

   # Pagination
   GET /api/users/?page=2&page_size=20

   # String matching
   GET /api/users/?email__like=%@example.com

Next Steps
----------

- Learn about :doc:`permissions` for access control
- Explore :doc:`crud` for advanced CRUD configuration
- See :doc:`user-models` for authentication and authorization
- Check the :doc:`api` reference for detailed documentation
