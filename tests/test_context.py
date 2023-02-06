from typing import Any

import pytest
from jinja2.exceptions import UndefinedError

from supertemplater.context import Context

TEST_DATA = {"name": "John", "age": 30}


@pytest.fixture
def default_ctx() -> Context:
    ctx = Context()
    return ctx


@pytest.fixture
def full_ctx() -> Context:
    ctx = Context()
    ctx.update(**TEST_DATA)
    return ctx


@pytest.mark.parametrize(
    "expected", [({"name": "John"}), ({"name": "John", "age": 30})]
)
def test_update(default_ctx: Context, expected: dict[str, Any]):
    assert default_ctx.variables == {}
    default_ctx.update(**expected)
    assert default_ctx.variables == expected


@pytest.mark.parametrize("content, expected", [("Hello {{ name }}", "Hello John")])
def test_render_replaces_variables(full_ctx: Context, content, expected):
    result = full_ctx.render(content)
    assert result == expected


@pytest.mark.parametrize(
    "content",
    [
        ("{{ missing }}"),
        ("{% if missing %} {% endif %}"),
        ("{% for x in missing %} {% endfor %}"),
    ],
)
def test_render_missing_variable(default_ctx: Context, content):
    with pytest.raises(UndefinedError):
        default_ctx.render(content)
