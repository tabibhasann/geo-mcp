"""In-memory workspace storage for multi-step spatial workflows."""

import json
from typing import Any

from .errors import safe_tool

_workspace: dict[str, dict[str, Any]] = {}


@safe_tool
def workspace_store(name: str, data: str, description: str | None = None) -> dict:
    """Store JSON data for later use in this server process."""
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}", "hint": "Data must be valid JSON."}

    _workspace[name] = {
        "data": data,
        "parsed": parsed,
        "description": description or "",
        "type": parsed.get("type") if isinstance(parsed, dict) else type(parsed).__name__,
    }
    return {
        "success": True,
        "name": name,
        "type": _workspace[name]["type"],
        "description": _workspace[name]["description"],
        "size": len(data),
    }


@safe_tool
def workspace_get(name: str) -> dict:
    """Retrieve a stored item by name."""
    if name not in _workspace:
        available = list(_workspace)
        return {"error": f"Result '{name}' not found", "available": available}

    item = _workspace[name]
    return {
        "success": True,
        "name": name,
        "data": item["data"],
        "type": item["type"],
        "description": item["description"],
    }


@safe_tool
def workspace_list() -> dict:
    """List stored workspace items."""
    return {
        "results": [
            {
                "name": name,
                "type": item["type"],
                "description": item["description"],
                "size": len(item["data"]),
            }
            for name, item in _workspace.items()
        ],
        "count": len(_workspace),
    }


@safe_tool
def workspace_clear(name: str | None = None) -> dict:
    """Clear one stored item, or the entire workspace when no name is provided."""
    if name is None:
        count = len(_workspace)
        _workspace.clear()
        return {"success": True, "cleared": "all", "count": count}

    if name not in _workspace:
        return {"error": f"Result '{name}' not found", "success": False}

    del _workspace[name]
    return {"success": True, "cleared": [name], "count": 1}


@safe_tool
def workspace_rename(old_name: str, new_name: str) -> dict:
    """Rename a stored workspace item."""
    if old_name not in _workspace:
        return {"error": f"Result '{old_name}' not found", "success": False}
    if new_name in _workspace:
        return {"error": f"Result '{new_name}' already exists", "success": False}

    _workspace[new_name] = _workspace.pop(old_name)
    return {"success": True, "old_name": old_name, "new_name": new_name}
