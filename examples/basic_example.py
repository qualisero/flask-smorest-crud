"""Basic Flask-Smorest CRUD Example.

This example demonstrates how to create a simple CRUD API using Flask-Smorest-CRUD
for a basic User model with automatic endpoint generation.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_smorest import Api
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from datetime import datetime

from flask_smorest_crud import CRUDBlueprint

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///basic_example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# API Configuration
app.config['API_TITLE'] = 'Basic CRUD API'
app.config['API_VERSION'] = 'v1'
app.config['OPENAPI_VERSION'] = '3.0.2'
app.config['OPENAPI_URL_PREFIX'] = '/'
app.config['OPENAPI_SWAGGER_UI_PATH'] = '/swagger-ui'
app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

# Initialize extensions
db = SQLAlchemy(app)
api = Api(app)


# Define Models
class User(db.Model):
    """User model with basic fields."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    age = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<User {self.username}>'


# Define Schemas
class UserSchema(SQLAlchemyAutoSchema):
    """Schema for User model serialization."""
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        dump_only_fields = ['id', 'created_at']


# Create CRUD Blueprint
users_blp = CRUDBlueprint(
    'users', __name__,
    model='User',
    schema='UserSchema',
    url_prefix='/api/users/'
)

# Register blueprint with API
api.register_blueprint(users_blp)


# Optional: Add custom endpoints to the blueprint
@users_blp.route('/active', methods=['GET'])
@users_blp.response(200, UserSchema(many=True))
def get_active_users():
    """Get all active users."""
    active_users = User.query.filter_by(is_active=True).all()
    return active_users


@users_blp.route('/<int:user_id>/toggle-status', methods=['PATCH'])
@users_blp.response(200, UserSchema)
@users_blp.admin_endpoint
def toggle_user_status(user_id):
    """Toggle user active status (Admin only)."""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return user


# Initialize database
@app.before_first_request
def create_tables():
    """Create database tables."""
    db.create_all()
    
    # Add sample data if tables are empty
    if User.query.count() == 0:
        sample_users = [
            User(
                username='alice',
                email='alice@example.com',
                first_name='Alice',
                last_name='Smith',
                age=28
            ),
            User(
                username='bob',
                email='bob@example.com',
                first_name='Bob',
                last_name='Johnson',
                age=35
            ),
            User(
                username='charlie',
                email='charlie@example.com',
                first_name='Charlie',
                last_name='Brown',
                age=42
            )
        ]
        
        for user in sample_users:
            db.session.add(user)
        db.session.commit()
        print("Sample data created!")


if __name__ == '__main__':
    print("Starting Flask-Smorest CRUD Example...")
    print("API documentation available at: http://localhost:5000/swagger-ui")
    print("\nAvailable endpoints:")
    print("- GET    /api/users/              # List all users (with filtering)")
    print("- POST   /api/users/              # Create new user")
    print("- GET    /api/users/<id>          # Get specific user")
    print("- PATCH  /api/users/<id>          # Update user")
    print("- DELETE /api/users/<id>          # Delete user")
    print("- GET    /api/users/active        # Get active users only")
    print("- PATCH  /api/users/<id>/toggle-status  # Toggle user status (Admin)")
    print("\nFiltering examples:")
    print("- /api/users/?is_active=true")
    print("- /api/users/?age__min=25&age__max=40")
    print("- /api/users/?created_at__from=2024-01-01")
    
    app.run(debug=True)