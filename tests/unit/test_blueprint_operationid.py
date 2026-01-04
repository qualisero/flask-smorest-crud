"""Unit tests for BlueprintOperationIdMixin."""

# pyright: reportAttributeAccessIssue=false

from typing import Any

from flask.views import MethodView

from flask_more_smorest.crud.blueprint_operationid import (
    HTTP_METHOD_OPERATION_MAP,
    BlueprintOperationIdMixin,
)


class TestBlueprintOperationIdMixin:
    """Tests for BlueprintOperationIdMixin class."""

    def test_mixin_inheritance(self) -> None:
        """Test that BlueprintOperationIdMixin inherits from Blueprint."""
        from flask_smorest import Blueprint

        assert issubclass(BlueprintOperationIdMixin, Blueprint)

    def test_route_method_exists(self) -> None:
        """Test that route method exists and can be called."""
        # Create a minimal mock app
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("test", __name__)
            assert hasattr(bp, "route")
            assert callable(bp.route)

    def test_default_operation_name_map_contains_common_methods(self) -> None:
        """HTTP_METHOD_OPERATION_MAP includes verbs we rely on."""
        assert HTTP_METHOD_OPERATION_MAP["get"] == "get"
        assert HTTP_METHOD_OPERATION_MAP["post"] == "create"
        assert HTTP_METHOD_OPERATION_MAP["patch"] == "update"

    def test_operation_id_generation_for_list_endpoint(self) -> None:
        """Test operationId generation for list endpoints."""
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("products", __name__)

            # Define a MethodView class
            @bp.route("/")
            class Products(MethodView):
                methods = ["GET"]

                def get(self) -> dict[str, list[Any]]:
                    return {"products": []}

            # Check that operationId was set
            get_method = Products.get
            apidoc = getattr(get_method, "_apidoc", {})
            assert "manual_doc" in apidoc
            assert "operationId" in apidoc["manual_doc"]
            assert apidoc["manual_doc"]["operationId"] == "listProducts"

    def test_operation_id_generation_handles_plural_class_names(self) -> None:
        """Plural MethodView class names should drop the trailing 's'."""
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("items", __name__)

            @bp.route("/")
            class Items(MethodView):
                methods = ["GET"]

                def get(self) -> dict[str, list[Any]]:
                    return {"items": []}

            get_method = Items.get
            apidoc = getattr(get_method, "_apidoc", {})
            assert "manual_doc" in apidoc
            assert apidoc["manual_doc"]["operationId"] == "listItems"

    def test_operation_id_generation_for_get_endpoint(self) -> None:
        """Test operationId generation for GET single item endpoint."""
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("products", __name__)

            @bp.route("/<int:product_id>")
            class Product(MethodView):
                methods = ["GET"]

                def get(self, product_id: int) -> dict[str, dict[str, Any]]:
                    return {"product": {}}

            get_method = Product.get
            apidoc = getattr(get_method, "_apidoc", {})
            assert "manual_doc" in apidoc
            assert "operationId" in apidoc["manual_doc"]
            assert apidoc["manual_doc"]["operationId"] == "getProduct"

    def test_operation_id_generation_for_post_endpoint(self) -> None:
        """Test operationId generation for POST endpoint."""
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("products", __name__)

            @bp.route("/")
            class Products(MethodView):
                methods = ["POST"]

                def post(self) -> dict[str, dict[str, Any]]:
                    return {"product": {}}

            post_method = Products.post
            apidoc = getattr(post_method, "_apidoc", {})
            assert "manual_doc" in apidoc
            assert "operationId" in apidoc["manual_doc"]
            assert apidoc["manual_doc"]["operationId"] == "createProducts"

    def test_operation_id_generation_for_patch_endpoint(self) -> None:
        """Test operationId generation for PATCH endpoint."""
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("products", __name__)

            @bp.route("/<int:product_id>")
            class Product(MethodView):
                methods = ["PATCH"]

                def patch(self, product_id: int) -> dict[str, dict[str, Any]]:
                    return {"product": {}}

            patch_method = Product.patch
            apidoc = getattr(patch_method, "_apidoc", {})
            assert "manual_doc" in apidoc
            assert "operationId" in apidoc["manual_doc"]
            assert apidoc["manual_doc"]["operationId"] == "updateProduct"

    def test_operation_id_generation_for_delete_endpoint(self) -> None:
        """Test operationId generation for DELETE endpoint."""
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("products", __name__)

            @bp.route("/<int:product_id>")
            class Product(MethodView):
                methods = ["DELETE"]

                def delete(self, product_id: int) -> tuple[str, int]:
                    return "", 204

            delete_method = Product.delete
            apidoc = getattr(delete_method, "_apidoc", {})
            assert "manual_doc" in apidoc
            assert "operationId" in apidoc["manual_doc"]
            assert apidoc["manual_doc"]["operationId"] == "deleteProduct"

    def test_operation_id_with_snake_case_class_name(self) -> None:
        """Test operationId generation with snake_case class name."""
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("product_reviews", __name__)

            @bp.route("/<int:review_id>")
            class ProductReview(MethodView):
                methods = ["GET"]

                def get(self, review_id: int) -> dict[str, dict[str, Any]]:
                    return {"review": {}}

            get_method = ProductReview.get
            apidoc = getattr(get_method, "_apidoc", {})
            assert "manual_doc" in apidoc
            assert "operationId" in apidoc["manual_doc"]
            assert apidoc["manual_doc"]["operationId"] == "getProductReview"

    def test_manual_operation_id_not_overridden(self) -> None:
        """Test that manually set operationId is not overridden."""
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("products", __name__)

            @bp.route("/<int:product_id>")
            class Product(MethodView):
                methods = ["GET"]

                @bp.doc(operationId="customGetProduct")
                def get(self, product_id: int) -> dict[str, dict[str, Any]]:
                    return {"product": {}}

            get_method = Product.get
            apidoc = getattr(get_method, "_apidoc", {})
            # Manual operationId should be preserved
            assert apidoc["manual_doc"]["operationId"] == "customGetProduct"

    def test_operation_id_for_function_route(self) -> None:
        """Test operationId generation for function-based routes."""
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            bp = BlueprintOperationIdMixin("test", __name__)

            @bp.route("/custom")
            def custom_endpoint() -> dict[str, str]:
                return {"message": "success"}

            # For function-based routes, use function name
            apidoc = getattr(custom_endpoint, "_apidoc", {})
            assert "manual_doc" in apidoc
            assert "operationId" in apidoc["manual_doc"]
            assert apidoc["manual_doc"]["operationId"] == "customEndpoint"
