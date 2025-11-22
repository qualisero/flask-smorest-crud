"""Utility functions for Flask-Smorest CRUD operations."""

from typing import Optional


def convert_snake_to_camel(word: str) -> str:
    """Convert snake_case string to CamelCase.

    Args:
        word: Snake case string to convert

    Returns:
        CamelCase version of the input string

    Example:
        >>> convert_snake_to_camel("user_profile")
        'UserProfile'
        >>> convert_snake_to_camel("simple")
        'simple'
    """
    if "_" not in word:
        return word
    return "".join(x.capitalize() or "_" for x in word.split("_"))
