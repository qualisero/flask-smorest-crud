# Flask-More-Smorest

[![PyPI version](https://badge.fury.io/py/flask-more-smorest.svg)](https://badge.fury.io/py/flask-more-smorest)
[![Python Support](https://img.shields.io/pypi/pyversions/flask-more-smorest.svg)](https://pypi.org/project/flask-more-smorest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful extension library for Flask-Smorest that provides automatic CRUD operations, enhanced blueprints with annotations, and advanced query filtering capabilities.

## Features

- 🚀 **Automatic CRUD Operations**: Generate complete RESTful APIs with minimal code
- 📝 **Enhanced Blueprints**: Additional decorators for public/admin endpoints
- 🔍 **Advanced Query Filtering**: Automatic filtering with range queries for dates
- 🏷️ **Operation ID Generation**: Automatic OpenAPI operationId generation
- 🐍 **Modern Python**: Full type hints and Python 3.11+ support
- ⚡ **SQLAlchemy 2.0**: Built for the latest SQLAlchemy patterns

## Quick Start

### Installation

```bash
pip install flask-more-smorest
```

### Basic Usage

```python
from flask import Flask
from flask_smorest import Api
from flask_more_smorest import CRUDBlueprint

app = Flask(__name__)
app.config['API_TITLE'] = 'My API'
app.config['API_VERSION'] = 'v1'
app.config['OPENAPI_VERSION'] = '3.0.2'

api = Api(app)

# Create a CRUD blueprint for your User model
users_blp = CRUDBlueprint(
    'users', __name__,
    model='User',           # Your SQLAlchemy model name
    schema='UserSchema',    # Your Marshmallow schema name
    url_prefix='/api/users/'
)

api.register_blueprint(users_blp)
```

This automatically creates the following endpoints:

- `GET /api/users/` - List all users (with filtering)
- `POST /api/users/` - Create a new user
- `GET /api/users/{user_id}` - Get a specific user
- `PATCH /api/users/{user_id}` - Update a user
- `DELETE /api/users/{user_id}` - Delete a user

### Enhanced Blueprints

```python
from flask_more_smorest import EnhancedBlueprint

# Regular enhanced blueprint with annotations
blp = EnhancedBlueprint('auth', __name__)

@blp.route('/login', methods=['POST'])
@blp.public_endpoint
def login():
    \"\"\"User login endpoint\"\"\"
    # This endpoint is marked as public in documentation
    pass

@blp.route('/admin/stats', methods=['GET'])
@blp.admin_endpoint  
def admin_stats():
    \"\"\"Get admin statistics\"\"\"
    # This endpoint is marked as admin-only in documentation
    pass
```

### Advanced Filtering

The library automatically generates filter schemas for your models:

```python
# For a User model with created_at datetime field
# Automatically supports:
GET /api/users/?created_at__from=2024-01-01&created_at__to=2024-12-31
GET /api/users/?age__min=18&age__max=65
GET /api/users/?status=active
```

## Configuration Options

### CRUDBlueprint Parameters

```python
CRUDBlueprint(
    'users',                    # Blueprint name
    __name__,                   # Import name
    model='User',               # SQLAlchemy model class name
    schema='UserSchema',        # Marshmallow schema class name
    url_prefix='/api/users/',   # URL prefix for all routes
    res_id='id',               # Primary key field name
    res_id_param='user_id',    # URL parameter name for resource ID
    skip_methods=['DELETE'],    # Skip certain CRUD operations
    methods={                   # Custom method configuration
        'GET': {'description': 'Get user details'},
        'POST': {'description': 'Create new user'}
    }
)
```

### Filtering Configuration

The query filtering automatically handles these field types:

- **DateTime/Date fields**: Converted to range filters (`__from`, `__to`)
- **Numeric fields**: Support min/max filtering (`__min`, `__max`)
- **String/Other fields**: Direct equality matching

## Examples

### Complete Flask App

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_smorest import Api
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_more_smorest import CRUDBlueprint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['API_TITLE'] = 'Example API'
app.config['API_VERSION'] = 'v1'
app.config['OPENAPI_VERSION'] = '3.0.2'

db = SQLAlchemy(app)
api = Api(app)

# Define your model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)

# Define your schema
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

# Create CRUD blueprint
users_blp = CRUDBlueprint(
    'users', __name__,
    model='User',
    schema='UserSchema'
)

api.register_blueprint(users_blp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
```

### Custom Methods

```python
# Add custom endpoints to your CRUD blueprint
@users_blp.route('/search', methods=['POST'])
@users_blp.arguments(UserSearchSchema)
@users_blp.response(200, UserSchema(many=True))
def search_users(search_params):
    \"\"\"Advanced user search\"\"\"
    # Your custom search logic
    pass

@users_blp.route('/<int:user_id>/activate', methods=['POST'])
@users_blp.response(200, UserSchema)
@users_blp.admin_endpoint
def activate_user(user_id):
    \"\"\"Activate a user account\"\"\"
    # Your activation logic
    pass
```

## Requirements

- Python 3.11+
- Flask 3.0+
- Flask-Smorest
- SQLAlchemy 2.0+
- Flask-SQLAlchemy 3.1+
- Marshmallow-SQLAlchemy 1.4+

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.