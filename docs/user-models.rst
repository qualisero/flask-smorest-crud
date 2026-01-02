User Models & Authentication
============================

Flask-More-Smorest includes a built-in user system with authentication, roles, and token management.

Overview
--------

The user system provides:

- Pre-built ``User`` model with email/password authentication
- Role-based access control with ``UserRole`` and ``DefaultUserRole``
- JWT token management with ``UserToken`` for refresh tokens
- Profile and timestamp mixins for extended user data
- Easy extension for custom user models

Basic Usage
-----------

Import and use the default user models:

.. code-block:: python

   from flask_more_smorest.perms import User, UserRole, DefaultUserRole

   # Create a user
   user = User(email="admin@example.com")
   user.set_password("secret123")
   user.save()

   # Assign admin role
   UserRole(user=user, role=DefaultUserRole.ADMIN).save()

   # Verify password
   if user.check_password("secret123"):
       print("Password correct!")

   # Check if user has a role
   if user.has_role(DefaultUserRole.ADMIN):
       print("User is an admin!")

User Model
----------

The ``User`` model provides:

Fields
^^^^^^

- ``email``: str - Unique email address (required)
- ``password_hash``: str - Bcrypt hashed password
- ``is_active``: bool - Whether user account is active (default: True)
- ``id``: UUID - Inherited from BasePermsModel
- ``created_at``, ``updated_at``: datetime - Inherited from BasePermsModel

Methods
^^^^^^^

Password Management:

.. code-block:: python

   user = User(email="user@example.com")
   
   # Set password (automatically hashed with bcrypt)
   user.set_password("my-secure-password")
   
   # Check password
   if user.check_password("my-secure-password"):
       print("Correct!")

Role Management:

.. code-block:: python

   # Check if user has a specific role
   if user.has_role(DefaultUserRole.ADMIN):
       print("Admin user")
   
   # Check if user has any role
   if user.has_role():
       print("User has at least one role")
   
   # Get all user roles
   roles = user.roles  # List of UserRole objects

Token Management:

.. code-block:: python

   # Get user's tokens
   tokens = user.tokens  # List of UserToken objects

Default Roles
-------------

``DefaultUserRole`` enum provides common roles:

.. code-block:: python

   from flask_more_smorest.perms import DefaultUserRole

   # Available roles
   DefaultUserRole.ADMIN       # Administrator
   DefaultUserRole.MODERATOR   # Moderator  
   DefaultUserRole.USER        # Regular user

Assigning Roles:

.. code-block:: python

   from flask_more_smorest.perms import User, UserRole, DefaultUserRole

   user = User.query.filter_by(email="user@example.com").first()
   
   # Add admin role
   UserRole(user=user, role=DefaultUserRole.ADMIN).save()
   
   # Add multiple roles
   UserRole(user=user, role=DefaultUserRole.MODERATOR).save()

Removing Roles:

.. code-block:: python

   # Find and delete specific role
   role = UserRole.query.filter_by(
       user_id=user.id,
       role=DefaultUserRole.MODERATOR
   ).first()
   if role:
       role.delete()

JWT Authentication
------------------

The user system integrates with Flask-JWT-Extended:

Configuration:

.. code-block:: python

   from flask import Flask
   from flask_more_smorest.perms import Api

   app = Flask(__name__)
   app.config.update(
       SECRET_KEY="your-secret-key",
       JWT_SECRET_KEY="your-jwt-secret",
       JWT_ACCESS_TOKEN_EXPIRES=3600,  # 1 hour
       JWT_REFRESH_TOKEN_EXPIRES=2592000,  # 30 days
   )

   api = Api(app)  # Automatically initializes JWT

Login Endpoint:

.. code-block:: python

   from flask import Blueprint
   from flask_jwt_extended import create_access_token, create_refresh_token
   from flask_more_smorest.perms import User

   auth = Blueprint("auth", __name__)

   @auth.route("/login", methods=["POST"])
   def login():
       data = request.get_json()
       user = User.query.filter_by(email=data["email"]).first()
       
       if not user or not user.check_password(data["password"]):
           return {"error": "Invalid credentials"}, 401
       
       if not user.is_active:
           return {"error": "Account disabled"}, 403
       
       access_token = create_access_token(identity=user.id)
       refresh_token = create_refresh_token(identity=user.id)
       
       return {
           "access_token": access_token,
           "refresh_token": refresh_token,
       }

Protected Endpoints:

.. code-block:: python

   from flask_jwt_extended import jwt_required, get_jwt_identity

   @auth.route("/profile")
   @jwt_required()
   def profile():
       user_id = get_jwt_identity()
       user = User.get_by_or_404(id=user_id)
       return UserSchema().dump(user)

Token Management
----------------

The ``UserToken`` model stores refresh tokens:

.. code-block:: python

   from flask_more_smorest.perms import UserToken
   from flask_jwt_extended import create_refresh_token

   # Create and store token
   refresh_token = create_refresh_token(identity=user.id)
   token = UserToken(
       user_id=user.id,
       token=refresh_token,
       expires_at=datetime.utcnow() + timedelta(days=30)
   )
   token.save()

   # Revoke token
   token.delete()

   # Clean up expired tokens
   UserToken.query.filter(
       UserToken.expires_at < datetime.utcnow()
   ).delete()

Extending User Model
--------------------

Create custom user models by inheriting from ``User``:

Basic Extension:

.. code-block:: python

   from flask_more_smorest.perms import User
   from flask_more_smorest.sqla import db
   from sqlalchemy.orm import Mapped, mapped_column

   class Employee(User):
       # Table name automatically set to "employee"
       # Override if needed: __tablename__ = "employees"
       
       employee_id: Mapped[str] = mapped_column(
           db.String(32), unique=True, nullable=False
       )
       department: Mapped[str] = mapped_column(db.String(100))
       hire_date: Mapped[datetime] = mapped_column(db.DateTime)

With Profile Mixin:

.. code-block:: python

   from flask_more_smorest.perms import User, ProfileMixin

   class Customer(ProfileMixin, User):
       # Table name automatically set to "customer"
       
       loyalty_points: Mapped[int] = mapped_column(db.Integer, default=0)
       # ProfileMixin adds: first_name, last_name, phone, address, etc.

With Timestamps Mixin:

.. code-block:: python

   from flask_more_smorest.perms import User, TimestampMixin

   class Member(TimestampMixin, User):
       # Table name automatically set to "member"
       
       membership_level: Mapped[str] = mapped_column(db.String(20))
       # TimestampMixin adds: created_at, updated_at

Multi-Tenant Users:

.. code-block:: python

   from flask_more_smorest.perms import User, HasDomainMixin
   import uuid

   class TenantUser(HasDomainMixin, User):
       # Table name automatically set to "tenant_user"
       
       # HasDomainMixin adds domain_id and domain relationship
       # for multi-tenant applications

Profile Mixin
-------------

``ProfileMixin`` adds common profile fields:

.. code-block:: python

   from flask_more_smorest.perms import ProfileMixin, User

   class UserProfile(ProfileMixin, User):
       # Table name automatically set to "user_profile"
       pass

Fields added by ProfileMixin:

- ``first_name``: str
- ``last_name``: str
- ``phone``: str (optional)
- ``address``: str (optional)
- ``city``: str (optional)
- ``state``: str (optional)
- ``postal_code``: str (optional)
- ``country``: str (optional)

Domain/Multi-Tenancy
--------------------

Use ``HasDomainMixin`` for multi-tenant applications:

.. code-block:: python

   from flask_more_smorest.perms import (
       BasePermsModel,
       HasDomainMixin,
       User,
   )

   # Domain model (tenant)
   class Organization(BasePermsModel):
       # Table name automatically set to "organization"
       
       name: Mapped[str] = mapped_column(db.String(200))
       slug: Mapped[str] = mapped_column(db.String(100), unique=True)

   # User with domain
   class OrgUser(HasDomainMixin, User):
       # Table name automatically set to "org_user"
       
       # Automatically adds:
       # - domain_id: UUID foreign key
       # - domain: relationship to Organization

   # Resource scoped to domain
   class OrgDocument(HasDomainMixin, BasePermsModel):
       # Table name automatically set to "org_document"
       
       title: Mapped[str] = mapped_column(db.String(200))
       # domain_id automatically added

Query by domain:

.. code-block:: python

   # Get users in specific organization
   org = Organization.get_by(slug="acme-corp")
   users = OrgUser.query.filter_by(domain_id=org.id).all()
   
   # Get documents for organization
   docs = OrgDocument.query.filter_by(domain_id=org.id).all()

Custom Roles
------------

Define custom roles for your application:

.. code-block:: python

   import enum
   from flask_more_smorest.perms import UserRole, User

   class CustomRole(enum.StrEnum):
       SUPER_ADMIN = "super_admin"
       EDITOR = "editor"
       VIEWER = "viewer"
       CONTRIBUTOR = "contributor"

   # Assign custom role
   user = User.get_by(email="editor@example.com")
   UserRole(user=user, role=CustomRole.EDITOR).save()

   # Check custom role
   if user.has_role(CustomRole.EDITOR):
       print("User is an editor")

Permission Integration
----------------------

User models integrate with the permission system:

.. code-block:: python

   from flask_more_smorest.perms import (
       BasePermsModel,
       HasUserMixin,
       UserOwnershipMixin,
   )

   class UserDocument(HasUserMixin, UserOwnershipMixin, BasePermsModel):
       # Table name automatically set to "user_document"
       # Uses default: __delegate_to_user__ = False (simple ownership)
       
       title: Mapped[str] = mapped_column(db.String(200))
       content: Mapped[str] = mapped_column(db.Text)
       
       # Permissions automatically enforced:
       # - Users can only access their own documents
       # - Admins can access all documents

Example: Complete Auth System
------------------------------

Here's a complete authentication system:

.. code-block:: python

   from flask import Flask, Blueprint, request
   from flask_jwt_extended import (
       create_access_token,
       create_refresh_token,
       jwt_required,
       get_jwt_identity,
   )
   from flask_more_smorest import init_db
   from flask_more_smorest.perms import (
       Api,
       User,
       UserRole,
       DefaultUserRole,
       CRUDBlueprint,
   )

   app = Flask(__name__)
   app.config.update(
       SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
       SECRET_KEY="secret",
       JWT_SECRET_KEY="jwt-secret",
   )

   init_db(app)
   api = Api(app)

   # Auth blueprint
   auth = Blueprint("auth", __name__, url_prefix="/auth")

   @auth.route("/register", methods=["POST"])
   def register():
       data = request.get_json()
       
       if User.query.filter_by(email=data["email"]).first():
           return {"error": "Email already exists"}, 400
       
       user = User(email=data["email"])
       user.set_password(data["password"])
       user.save()
       
       # Assign default user role
       UserRole(user=user, role=DefaultUserRole.USER).save()
       
       return {"message": "User created"}, 201

   @auth.route("/login", methods=["POST"])
   def login():
       data = request.get_json()
       user = User.query.filter_by(email=data["email"]).first()
       
       if not user or not user.check_password(data["password"]):
           return {"error": "Invalid credentials"}, 401
       
       access_token = create_access_token(identity=str(user.id))
       refresh_token = create_refresh_token(identity=str(user.id))
       
       return {
           "access_token": access_token,
           "refresh_token": refresh_token,
       }

   @auth.route("/profile")
   @jwt_required()
   def profile():
       user_id = get_jwt_identity()
       user = User.get_by_or_404(id=user_id)
       return {
           "id": str(user.id),
           "email": user.email,
           "is_active": user.is_active,
           "roles": [role.role for role in user.roles],
       }

   app.register_blueprint(auth)

   # Users management (admin only)
   users_bp = CRUDBlueprint(
       "users",
       __name__,
       model=User,
       schema=User.Schema,
       url_prefix="/api/users/",
       methods={
           CRUDMethod.DELETE: {"admin_only": True},
           CRUDMethod.PATCH: {"admin_only": True},
       },
   )

   api.register_blueprint(users_bp)

Next Steps
----------

- Learn about :doc:`permissions` for access control
- See :doc:`crud` for creating user management endpoints
- Check the :doc:`api` reference for detailed model documentation
