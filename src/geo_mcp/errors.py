"""Tool-safe error handling utilities."""

from collections.abc import Callable
from functools import wraps
from typing import Any


def safe_tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that catches all exceptions and returns tool-safe error dicts.

    Returns raw values for successful results, error dicts for exceptions.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            return {"error": str(e), "hint": "Check your input parameters."}
        except ImportError as e:
            hint = "Install required extras: pip install mcp-geo[files] or mcp-geo[raster]"
            return {"error": str(e), "hint": hint}
        except Exception as e:
            return {"error": str(e), "hint": "An unexpected error occurred."}

    return wrapper


def async_safe_tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Async variant of safe_tool."""

    @wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except ValueError as e:
            return {"error": str(e), "hint": "Check your input parameters."}
        except ImportError as e:
            hint = "Install required extras: pip install mcp-geo[files] or mcp-geo[raster]"
            return {"error": str(e), "hint": hint}
        except Exception as e:
            return {"error": str(e), "hint": "An unexpected error occurred."}

    return wrapper
