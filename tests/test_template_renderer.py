from pathlib import Path

import pytest

from mixy.application.services import TemplateRenderer
from mixy.domain.exceptions import RenderingError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "templates"


def test_render_file_renders_text_content() -> None:
    renderer = TemplateRenderer()

    rendered = renderer.render_file(
        FIXTURES_DIR / "hello.txt",
        {"name": "World"},
    )

    assert rendered.rendered is True
    assert rendered.is_binary is False
    assert rendered.content.decode() == "Hello World\n"


def test_render_file_wraps_undefined_errors() -> None:
    renderer = TemplateRenderer()

    with pytest.raises(RenderingError) as error:
        renderer.render_file(FIXTURES_DIR / "hello.txt", {})

    assert error.value.variable_name == "name"
    assert "hello.txt" in error.value.file_path


def test_render_path_renders_names() -> None:
    renderer = TemplateRenderer()

    assert renderer.render_path("{{ project_name }}", {"project_name": "my_app"}) == "my_app"
    assert renderer.render_path("{{ module }}.py", {"module": "utils"}) == "utils.py"


def test_render_path_strips_j2_suffix() -> None:
    renderer = TemplateRenderer()

    assert renderer.render_path("Dockerfile.j2", {}) == "Dockerfile"
    assert renderer.render_path("config.yaml.j2", {}) == "config.yaml"


def test_render_policy_exclude_pattern_skips_rendering() -> None:
    renderer = TemplateRenderer()
    expected = (FIXTURES_DIR / "app.min.js").read_bytes()

    rendered = renderer.render_file(
        FIXTURES_DIR / "app.min.js",
        {"name": "World"},
        {"exclude": ["*.min.js"]},
    )

    assert rendered.rendered is False
    assert rendered.content == expected


def test_include_patterns_gate_rendering_when_text_rendering_disabled() -> None:
    renderer = TemplateRenderer()

    rendered = renderer.render_file(
        FIXTURES_DIR / "hello.txt",
        {"name": "World"},
        {"include": ["*.md"]},
        render_text_files=False,
    )

    assert rendered.rendered is False


def test_copy_mode_raw_skips_rendering() -> None:
    renderer = TemplateRenderer()

    rendered = renderer.render_file(
        FIXTURES_DIR / "hello.txt",
        {"name": "World"},
        copy_mode="raw",
    )

    assert rendered.rendered is False


def test_j2_suffix_forces_rendering() -> None:
    renderer = TemplateRenderer()

    rendered = renderer.render_file(
        FIXTURES_DIR / "Dockerfile.j2",
        {"python_version": "3.12"},
        {"exclude": ["*.j2"]},
    )

    assert rendered.output_name == "Dockerfile"
    assert rendered.rendered is True
    assert rendered.content.decode() == "FROM python:3.12\n"


def test_render_path_segment_can_leave_names_unrendered() -> None:
    renderer = TemplateRenderer()

    assert (
        renderer.render_path_segment(
            "{{ project_name }}",
            {"project_name": "my_app"},
            enabled=False,
        )
        == "{{ project_name }}"
    )


def test_integration_renders_mixed_template_directory() -> None:
    renderer = TemplateRenderer()
    root = FIXTURES_DIR
    context = {
        "module": "utils",
        "name": "World",
        "project_name": "my_app",
        "python_version": "3.12",
    }

    rendered_files: dict[str, tuple[bool, bytes]] = {}
    for source_path in root.rglob("*"):
        if not source_path.is_file():
            continue

        relative_path = source_path.relative_to(root)
        rendered_parts = [renderer.render_path(part, context) for part in relative_path.parts[:-1]]
        rendered_file = renderer.render_file(
            source_path,
            context,
            {"exclude": ["*.png"]},
        )
        final_path = "/".join([*rendered_parts, rendered_file.output_name])
        rendered_files[final_path] = (rendered_file.rendered, rendered_file.content)

    assert rendered_files["hello.txt"] == (True, b"Hello World\n")
    assert rendered_files["Dockerfile"] == (True, b"FROM python:3.12\n")
    assert rendered_files["app.min.js"][0] is True
    assert rendered_files["logo.png"][0] is False
    assert rendered_files["nested/my_app/module.py"][1].decode().endswith('"World"\n')
