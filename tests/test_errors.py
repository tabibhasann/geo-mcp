"""Tests for error handling decorators."""

from geo_mcp.errors import async_safe_tool, safe_tool


class TestSafeTool:
    def test_success_returns_value(self):
        @safe_tool
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_value_error_returns_error_dict(self):
        @safe_tool
        def fail():
            raise ValueError("bad input")

        result = fail()
        assert "error" in result
        assert "bad input" in result["error"]
        assert "hint" in result

    def test_import_error_returns_hint(self):
        @safe_tool
        def fail():
            raise ImportError("shapely not found")

        result = fail()
        assert "error" in result
        assert "shapely not found" in result["error"]
        assert "pip install" in result["hint"]

    def test_unexpected_error_returns_error_dict(self):
        @safe_tool
        def fail():
            raise RuntimeError("unexpected")

        result = fail()
        assert "error" in result
        assert "unexpected" in result["error"]

    def test_preserves_function_name(self):
        @safe_tool
        def my_function():
            return 42

        assert my_function.__name__ == "my_function"


class TestAsyncSafeTool:
    async def test_success_returns_value(self):
        @async_safe_tool
        async def add(a, b):
            return a + b

        assert await add(2, 3) == 5

    async def test_value_error_returns_error_dict(self):
        @async_safe_tool
        async def fail():
            raise ValueError("bad input")

        result = await fail()
        assert "error" in result
        assert "bad input" in result["error"]

    async def test_unexpected_error_returns_error_dict(self):
        @async_safe_tool
        async def fail():
            raise RuntimeError("unexpected")

        result = await fail()
        assert "error" in result
        assert "unexpected" in result["error"]
