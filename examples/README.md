# Flask-More-Smorest Examples

This directory contains example applications demonstrating the usage of Flask-More-Smorest extensions.

## Examples

### 1. Basic Example (`basic_example.py`)

A simple demonstration of automatic CRUD operations with a User model.

**Features:**
- Basic User model with common fields
- Automatic CRUD endpoints generation
- Custom endpoints with public/admin annotations
- Filtering capabilities
- Sample data initialization

**Run:**
```bash
cd examples
python basic_example.py
```

**Access:** http://localhost:5000/swagger-ui

### 2. Advanced Example (`advanced_example.py`)

A comprehensive example showing advanced features with multiple related models.

**Features:**
- Multiple models with relationships (Category, Product, Order)
- Custom validation and search functionality
- Public and Admin endpoint annotations
- Advanced filtering and relationships
- Soft delete functionality
- Administrative operations

**Run:**
```bash
cd examples
python advanced_example.py
```

**Access:** http://localhost:5001/docs

## Available Endpoints

### Basic Example
- `GET /api/users/` - List all users (with filtering)
- `POST /api/users/` - Create new user  
- `GET /api/users/{id}` - Get specific user
- `PATCH /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user
- `GET /api/users/active` - Get active users only (custom)
- `PATCH /api/users/{id}/toggle-status` - Toggle user status (admin)

### Advanced Example
- **Categories:** Full CRUD operations at `/api/categories/`
- **Products:** CRUD with soft delete at `/api/products/`
- **Orders:** Read-only operations at `/api/orders/`
- **Search:** `POST /api/products/search` - Advanced product search
- **Admin:** Administrative endpoints at `/api/admin/`

## Filtering Examples

Both examples support advanced filtering:

```bash
# Filter by boolean fields
GET /api/users/?is_active=true

# Range filtering for numeric fields
GET /api/users/?age__min=25&age__max=40

# Date range filtering
GET /api/users/?created_at__from=2024-01-01&created_at__to=2024-12-31

# Product filtering (advanced example)
GET /api/products/?price__min=50&price__max=500&is_available=true
```

## Requirements

Both examples require the same dependencies as the main package:

```bash
pip install flask-more-smorest
```

Or for development:

```bash
poetry install
cd examples
python basic_example.py
```

## Database

Examples use SQLite databases that are created automatically:
- Basic: `basic_example.db`
- Advanced: `advanced_example.db`

The databases are populated with sample data on first run.

## Extending Examples

These examples serve as starting points for your own applications. You can:

1. **Add new models** and their corresponding CRUD blueprints
2. **Customize validation** by extending the schema classes
3. **Add authentication** using Flask-JWT-Extended or similar
4. **Implement pagination** for large datasets
5. **Add custom business logic** in additional endpoint methods

## Tips

1. **Documentation:** Both examples include Swagger UI for interactive API documentation
2. **Debugging:** Run with `debug=True` for development
3. **Testing:** Use the generated OpenAPI specs for automated testing
4. **Production:** Remember to configure proper database URIs and secrets for production use