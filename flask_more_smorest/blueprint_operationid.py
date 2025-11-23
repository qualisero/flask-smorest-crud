"""Enhanced Blueprint with additional decorators and functionality."""

from typing import Callable, Any
from flask_smorest import Blueprint

from .utils import convert_snake_to_camel


class BlueprintOperationIdMixin(Blueprint):
    """This class extends Flask-Smorest's Blueprint to support
    automatic operationId generation.
    """

    def route(self, rule: str, *pargs: Any, **kwargs: Any) -> Callable[..., Any]:
        """Override route to add automatic operationId.

        Args:
            rule: URL rule for the route
            *pargs: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Decorated route function
        """
        wrapped = super().route(rule, *pargs, **kwargs)

        OPERATION_NAME_MAP = {"patch": "update", "delete": "delete", "get": "get", "post": "create", "put": "replace"}

        def _add_operation_id(func: Callable[..., Any], method_view_class: type | None = None) -> Callable[..., Any]:
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

        def _route(class_or_func: Any) -> Any:
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
