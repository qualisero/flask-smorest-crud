from flask_smorest import Blueprint 

from .utils import convert_snake_to_camel


class EnhancedBlueprint(Blueprint):
    """Blueprint with added annotations."""

    def public_endpoint(self, function):
        """Decorator to mark an endpoint as public."""
        function._is_public = True
        function.__doc__ += " | 🌐 Public"
        return function

    def admin_endpoint(self, func):
        """Decorator to mark an endpoint as admin only."""
        func._is_admin = True
        if func.__doc__ is None:
            func.__doc__ = "Admin only endpoint"
        else:
            func.__doc__ += " | 🔑 Admin only"
        return func

    def route(self, rule, *pargs, **kwargs):
        """Override route to add automatic operationId."""
        wrapped = super().route(rule, *pargs, **kwargs)

        OPERATION_NAME_MAP = {"patch": "update", "delete": "delete", "get": "get", "post": "create", "put": "replace"}

        def _add_operation_id(func, method_view_class=None):
            """Add operationId to the function if not already set."""
            apidoc = getattr(func, "_apidoc", {})
            if "manual_doc" in apidoc and "operationId" in apidoc["manual_doc"]:
                return func
            if method_view_class is None:
                operation_id = func.__name__
            else:
                if func.__name__.lower() == "get" and method_view_class.__name__.endswith("s") and rule.endswith("/"):
                    operation_id = f"list{method_view_class.__name__[:-1]}"
                else:
                    operation_name = OPERATION_NAME_MAP.get(func.__name__.lower(), func.__name__.lower())
                    operation_id = f"{operation_name}{method_view_class.__name__}"
            operation_id = convert_snake_to_camel(operation_id)
            operation_id = operation_id[0].lower() + operation_id[1:]
            return self.doc(operationId=operation_id)(func)

        def _route(class_or_func):
            """Add operationId to the route's methods."""
            if hasattr((class_or_func), "methods"):
                for method in class_or_func.methods:
                    method_fn = getattr(class_or_func, method.lower(), None)
                    if not method_fn:
                        continue
                    method_fn = _add_operation_id(method_fn, class_or_func)
                    setattr(class_or_func, method.lower(), method_fn)
            else:
                class_or_func = _add_operation_id(class_or_func)
            return wrapped(class_or_func)

        return _route
