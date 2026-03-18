import pytest
from jinja2 import UndefinedError

from mixy.infrastructure.rendering.jinja_renderer import (
    has_jinja_suffix,
    render_string,
    strip_jinja_suffix,
)


def test_render_string_supports_substitution_conditionals_and_loops() -> None:
    template = (
        "Hello {{ name }}\n"
        "{% if use_docker %}Dockerfile{% endif %}\n"
        "{% for item in items %}{{ item }} {% endfor %}"
    )

    rendered = render_string(
        template,
        {"items": ["a", "b"], "name": "World", "use_docker": True},
    )

    assert "Hello World" in rendered
    assert "Dockerfile" in rendered
    assert "a b" in rendered


def test_render_string_uses_strict_undefined() -> None:
    with pytest.raises(UndefinedError):
        render_string("Hello {{ missing }}", {})


def test_jinja_suffix_helpers() -> None:
    assert has_jinja_suffix("Dockerfile.j2") is True
    assert strip_jinja_suffix("Dockerfile.j2") == "Dockerfile"
    assert strip_jinja_suffix("config.yaml.j2") == "config.yaml"
    assert has_jinja_suffix("README.md") is False
