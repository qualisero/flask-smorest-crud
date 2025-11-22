"""Advanced Flask-More-Smorest Example.

This example demonstrates advanced features including:
- Multiple related models with relationships
- Custom filtering and validation
- Public/Admin endpoint annotations
- Enhanced blueprint features
"""

from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_smorest import Api, Blueprint
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, Schema, validates_schema, ValidationError
from datetime import datetime
from typing import List, Dict, Any

from flask_more_smorest import CRUDBlueprint, EnhancedBlueprint

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "advanced-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///advanced_example.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# API Configuration
app.config["API_TITLE"] = "Advanced CRUD API"
app.config["API_VERSION"] = "v2"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"

# Initialize extensions
db = SQLAlchemy(app)
api = Api(app)


# Define Models with Relationships
class Category(db.Model):
    """Product category model."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship
    products = db.relationship("Product", backref="category", lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    """Product model with category relationship."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Product {self.name}>"


class Order(db.Model):
    """Order model."""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, confirmed, shipped, delivered, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shipped_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Order {self.id} - {self.customer_name}>"


# Define Schemas with Validation
class CategorySchema(SQLAlchemyAutoSchema):
    """Category schema with validation."""

    class Meta:
        model = Category
        load_instance = True
        include_fk = True
        dump_only_fields = ["id", "created_at"]

    products = fields.Nested("ProductSchema", many=True, exclude=["category"], dump_only=True)

    @validates_schema
    def validate_category(self, data, **kwargs):
        """Custom validation for category data."""
        if "name" in data and len(data["name"]) < 2:
            raise ValidationError("Category name must be at least 2 characters long.")


class ProductSchema(SQLAlchemyAutoSchema):
    """Product schema with advanced validation."""

    class Meta:
        model = Product
        load_instance = True
        include_fk = True
        dump_only_fields = ["id", "created_at", "updated_at"]

    category = fields.Nested(CategorySchema, exclude=["products"], dump_only=True)

    @validates_schema
    def validate_product(self, data, **kwargs):
        """Custom validation for product data."""
        if "price" in data and data["price"] <= 0:
            raise ValidationError("Product price must be greater than 0.")
        if "stock_quantity" in data and data["stock_quantity"] < 0:
            raise ValidationError("Stock quantity cannot be negative.")


class OrderSchema(SQLAlchemyAutoSchema):
    """Order schema."""

    class Meta:
        model = Order
        load_instance = True
        dump_only_fields = ["id", "created_at"]

    @validates_schema
    def validate_order(self, data, **kwargs):
        """Custom validation for order data."""
        if "total_amount" in data and data["total_amount"] <= 0:
            raise ValidationError("Order total must be greater than 0.")

        valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
        if "status" in data and data["status"] not in valid_statuses:
            raise ValidationError(f"Status must be one of: {valid_statuses}")


# Custom Search Schema
class ProductSearchSchema(Schema):
    """Schema for product search parameters."""

    name = fields.String(missing=None)
    category_id = fields.Integer(missing=None)
    min_price = fields.Decimal(missing=None)
    max_price = fields.Decimal(missing=None)
    in_stock = fields.Boolean(missing=None)
    available = fields.Boolean(missing=None)


# Create CRUD Blueprints
categories_blp = CRUDBlueprint(
    "categories", __name__, model="Category", schema="CategorySchema", url_prefix="/api/categories/"
)

products_blp = CRUDBlueprint(
    "products",
    __name__,
    model="Product",
    schema="ProductSchema",
    url_prefix="/api/products/",
    # Skip DELETE for products (soft delete instead)
    skip_methods=["DELETE"],
)

orders_blp = CRUDBlueprint(
    "orders",
    __name__,
    model="Order",
    schema="OrderSchema",
    url_prefix="/api/orders/",
    # Only allow GET and POST for orders
    methods=["GET", "POST", "INDEX"],
)

# Create additional blueprint for admin functions
admin_blp = EnhancedBlueprint("admin", __name__, url_prefix="/api/admin/")


# Add custom endpoints to blueprints
@products_blp.route("/search", methods=["POST"])
@products_blp.arguments(ProductSearchSchema)
@products_blp.response(200, ProductSchema(many=True))
@products_blp.public_endpoint
def search_products(search_params):
    """Advanced product search with multiple criteria."""
    query = Product.query

    if search_params.get("name"):
        query = query.filter(Product.name.ilike(f"%{search_params['name']}%"))

    if search_params.get("category_id"):
        query = query.filter(Product.category_id == search_params["category_id"])

    if search_params.get("min_price"):
        query = query.filter(Product.price >= search_params["min_price"])

    if search_params.get("max_price"):
        query = query.filter(Product.price <= search_params["max_price"])

    if search_params.get("in_stock") is not None:
        if search_params["in_stock"]:
            query = query.filter(Product.stock_quantity > 0)
        else:
            query = query.filter(Product.stock_quantity == 0)

    if search_params.get("available") is not None:
        query = query.filter(Product.is_available == search_params["available"])

    return query.all()


@products_blp.route("/<int:product_id>/soft-delete", methods=["DELETE"])
@products_blp.response(200, ProductSchema)
@products_blp.admin_endpoint
def soft_delete_product(product_id):
    """Soft delete a product (Admin only)."""
    product = Product.query.get_or_404(product_id)
    product.is_available = False
    db.session.commit()
    return product


@orders_blp.route("/<int:order_id>/ship", methods=["PATCH"])
@orders_blp.response(200, OrderSchema)
@orders_blp.admin_endpoint
def ship_order(order_id):
    """Mark order as shipped (Admin only)."""
    order = Order.query.get_or_404(order_id)
    if order.status != "confirmed":
        abort(400, description="Can only ship confirmed orders")

    order.status = "shipped"
    order.shipped_at = datetime.utcnow()
    db.session.commit()
    return order


# Admin-only endpoints
@admin_blp.route("/stats", methods=["GET"])
@admin_blp.response(200)
@admin_blp.admin_endpoint
def get_admin_stats():
    """Get administrative statistics (Admin only)."""
    stats = {
        "total_products": Product.query.count(),
        "available_products": Product.query.filter_by(is_available=True).count(),
        "total_categories": Category.query.filter_by(is_active=True).count(),
        "total_orders": Order.query.count(),
        "pending_orders": Order.query.filter_by(status="pending").count(),
        "shipped_orders": Order.query.filter_by(status="shipped").count(),
        "low_stock_products": Product.query.filter(Product.stock_quantity < 10).count(),
    }
    return stats


@admin_blp.route("/products/restock", methods=["POST"])
@admin_blp.arguments(Schema.from_dict({"product_id": fields.Integer(), "quantity": fields.Integer()}))
@admin_blp.response(200, ProductSchema)
@admin_blp.admin_endpoint
def restock_product(restock_data):
    """Restock a product (Admin only)."""
    product = Product.query.get_or_404(restock_data["product_id"])
    product.stock_quantity += restock_data["quantity"]
    db.session.commit()
    return product


# Register all blueprints
api.register_blueprint(categories_blp)
api.register_blueprint(products_blp)
api.register_blueprint(orders_blp)
api.register_blueprint(admin_blp)


# Initialize database
@app.before_first_request
def create_tables():
    """Create database tables with sample data."""
    db.create_all()

    # Add sample data
    if Category.query.count() == 0:
        categories = [
            Category(name="Electronics", description="Electronic devices and gadgets"),
            Category(name="Books", description="Books and educational materials"),
            Category(name="Clothing", description="Apparel and fashion items"),
        ]

        for category in categories:
            db.session.add(category)
        db.session.commit()

        products = [
            Product(
                name="Laptop", description="High-performance laptop", price=999.99, stock_quantity=50, category_id=1
            ),
            Product(
                name="Smartphone",
                description="Latest smartphone model",
                price=699.99,
                stock_quantity=100,
                category_id=1,
            ),
            Product(
                name="Python Programming Book",
                description="Learn Python programming",
                price=49.99,
                stock_quantity=25,
                category_id=2,
            ),
            Product(
                name="T-Shirt", description="Comfortable cotton t-shirt", price=19.99, stock_quantity=200, category_id=3
            ),
        ]

        for product in products:
            db.session.add(product)
        db.session.commit()

        print("Sample data created!")


if __name__ == "__main__":
    print("Starting Advanced Flask-More-Smorest Example...")
    print("API documentation available at: http://localhost:5000/docs")
    print("\nFeatures demonstrated:")
    print("- Multiple related models (Category, Product, Order)")
    print("- Custom validation and search functionality")
    print("- Public and Admin endpoint annotations")
    print("- Advanced filtering and relationships")
    print("- Soft delete functionality")
    print("- Administrative statistics and operations")

    app.run(debug=True, port=5001)
