"""Tool-safe error handling utilities."""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any


def _relax_return_type(wrapper: Callable[..., Any], fn: Callable[..., Any]) -> None:
    wrapper.__annotations__ = dict(getattr(fn, "__annotations__", {}))
    wrapper.__annotations__["return"] = Any
    wrapper.__signature__ = inspect.signature(fn).replace(return_annotation=Any)  # type: ignore[attr-defined]


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
            hint = "Install the relevant extra, for example: pip install 'mcp-geo[files,raster,visual]'"
            return {"error": str(e), "hint": hint}
        except Exception as e:
            return {"error": str(e), "hint": "An unexpected error occurred."}

    _relax_return_type(wrapper, fn)
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
            hint = "Install the relevant extra, for example: pip install 'mcp-geo[files,raster,visual]'"
            return {"error": str(e), "hint": hint}
        except Exception as e:
            return {"error": str(e), "hint": "An unexpected error occurred."}

    _relax_return_type(wrapper, fn)
    return wrapper
