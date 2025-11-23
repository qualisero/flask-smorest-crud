"""Blueprint Mixin to support method annotation."""

from typing import Callable, Any


class PermsBlueprintMixin:
    """Blueprint with added annotations for public and admin endpoints.

    This class extends Flask-Smorest's Blueprint to provide additional
    decorators for marking endpoints with special access levels.
    """

    def public_endpoint(self, function: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to mark an endpoint as public.

        Args:
            function: The endpoint function to mark as public

        Returns:
            The decorated function with public annotation
        """
        function._is_public = True
        if function.__doc__ is None:
            function.__doc__ = "Public endpoint"
        else:
            function.__doc__ += " | 🌐 Public"
        return function

    def admin_endpoint(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to mark an endpoint as admin only.

        Args:
            func: The endpoint function to mark as admin only

        Returns:
            The decorated function with admin annotation
        """
        func._is_admin = True
        if func.__doc__ is None:
            func.__doc__ = "Admin only endpoint"
        else:
            func.__doc__ += " | 🔑 Admin only"
        return func
