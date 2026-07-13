"""Tests for workspace storage tools."""

from geo_mcp.workspace import (
    _workspace,
    workspace_clear,
    workspace_get,
    workspace_list,
    workspace_rename,
    workspace_store,
)


class TestWorkspaceStore:
    def setup_method(self):
        _workspace.clear()

    def teardown_method(self):
        _workspace.clear()

    def test_store_valid_json(self):
        result = workspace_store("test", '{"type": "Point", "coordinates": [0, 0]}')
        assert result["success"] is True
        assert result["name"] == "test"
        assert result["type"] == "Point"

    def test_store_with_description(self):
        result = workspace_store("test", '{"type": "Point"}', description="my point")
        assert result["description"] == "my point"

    def test_store_invalid_json(self):
        result = workspace_store("bad", "not json{")
        assert "error" in result
        assert "Invalid JSON" in result["error"]

    def test_store_array_json(self):
        result = workspace_store("arr", '[1, 2, 3]')
        assert result["success"] is True
        assert result["type"] == "list"


class TestWorkspaceGet:
    def setup_method(self):
        _workspace.clear()
        workspace_store("item1", '{"type": "Point"}')

    def teardown_method(self):
        _workspace.clear()

    def test_get_existing(self):
        result = workspace_get("item1")
        assert result["success"] is True
        assert result["name"] == "item1"
        assert "data" in result

    def test_get_missing(self):
        result = workspace_get("nonexistent")
        assert "error" in result
        assert "available" in result


class TestWorkspaceList:
    def setup_method(self):
        _workspace.clear()
        workspace_store("a", '{"type": "Point"}')
        workspace_store("b", '{"type": "LineString"}')

    def teardown_method(self):
        _workspace.clear()

    def test_list_returns_all(self):
        result = workspace_list()
        assert result["count"] == 2
        names = [r["name"] for r in result["results"]]
        assert "a" in names
        assert "b" in names

    def test_list_empty(self):
        _workspace.clear()
        result = workspace_list()
        assert result["count"] == 0
        assert result["results"] == []


class TestWorkspaceClear:
    def setup_method(self):
        _workspace.clear()
        workspace_store("a", '{"type": "Point"}')
        workspace_store("b", '{"type": "LineString"}')

    def teardown_method(self):
        _workspace.clear()

    def test_clear_single(self):
        result = workspace_clear("a")
        assert result["success"] is True
        assert result["count"] == 1
        assert "b" in _workspace
        assert "a" not in _workspace

    def test_clear_all(self):
        result = workspace_clear()
        assert result["success"] is True
        assert result["cleared"] == "all"
        assert result["count"] == 2
        assert len(_workspace) == 0

    def test_clear_missing(self):
        result = workspace_clear("nonexistent")
        assert "error" in result


class TestWorkspaceRename:
    def setup_method(self):
        _workspace.clear()
        workspace_store("old", '{"type": "Point"}')

    def teardown_method(self):
        _workspace.clear()

    def test_rename_success(self):
        result = workspace_rename("old", "new")
        assert result["success"] is True
        assert "new" in _workspace
        assert "old" not in _workspace

    def test_rename_missing_source(self):
        result = workspace_rename("nonexistent", "new")
        assert "error" in result

    def test_rename_target_exists(self):
        workspace_store("new", '{"type": "LineString"}')
        result = workspace_rename("old", "new")
        assert "error" in result
        assert "already exists" in result["error"]
