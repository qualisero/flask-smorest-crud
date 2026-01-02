.. flask-more-smorest documentation master file

Flask-More-Smorest Documentation
=================================

Flask-More-Smorest extends **Flask-Smorest** with batteries-included CRUD blueprints, 
SQLAlchemy helpers, and an opinionated user/permission system.

Features
--------

- **Automatic CRUD endpoints** with filtering and pagination
- **Blueprint mixins** for public/admin annotations and operation IDs
- **SQLAlchemy base model** with Marshmallow schemas and permission hooks
- **Optional JWT-powered** user, role, and token models

Quick Example
-------------

.. code-block:: python

   from flask import Flask
   from flask_more_smorest import init_db
   from flask_more_smorest.perms import Api, CRUDBlueprint

   app = Flask(__name__)
   app.config.update(
       SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
       SECRET_KEY="secret",
       JWT_SECRET_KEY="jwt-secret",
   )

   init_db(app)
   api = Api(app)

   # Automatic CRUD endpoints
   users = CRUDBlueprint(
       "users",
       __name__,
       model="User",
       schema="UserSchema",
       url_prefix="/api/users/",
   )

   api.register_blueprint(users)

This automatically creates RESTful endpoints with filtering, pagination, and permission checks.

.. note::

   **Automatic Table Naming**: When using ``BaseModel`` or its subclasses 
   (like ``BasePermsModel``, ``User``), you don't need to specify ``__tablename__``. 
   SQLAlchemy automatically generates table names by converting your class name to snake_case:
   
   - ``User`` → ``user``
   - ``UserProfile`` → ``user_profile``
   - ``ArticleComment`` → ``article_comment``
   
   Only specify ``__tablename__`` if you need a custom table name.

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   getting-started
   permissions
   crud
   user-models

.. toctree::
   :maxdepth: 3
   :caption: API Reference:

   api

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources:

   user-extension-guide

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


