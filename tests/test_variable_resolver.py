from pathlib import Path

import pytest
from loguru import logger

from mixy.domain.enums import VariableType
from mixy.domain.exceptions import VariableResolutionError
from mixy.domain.models import VariableDefinition
from mixy.domain.services import VariableResolver
from mixy.infrastructure.config import load_vars_file

VARS_FIXTURE = Path(__file__).parent / "fixtures" / "vars" / "basic.yml"


def test_precedence_chain_resolves_in_expected_order() -> None:
    resolver = VariableResolver()
    definitions = {
        "project_name": VariableDefinition(type=VariableType.STR, default="default"),
        "port": VariableDefinition(type=VariableType.INT, default=8000),
    }

    resolved = resolver.resolve_all(
        definitions,
        global_values={"port": 8100},
        source_values={"project_name": "source", "port": 8200},
        cli_overrides={"project_name": "cli"},
        vars_file_values={"project_name": "file", "port": 8150},
        environ={"MIXY_VAR_PROJECT_NAME": "env", "MIXY_VAR_PORT": "8050"},
    )

    assert resolved == {"project_name": "cli", "port": 8200}


def test_type_coercion_handles_int_float_and_bool() -> None:
    resolver = VariableResolver()
    definitions = {
        "count": VariableDefinition(type=VariableType.INT),
        "ratio": VariableDefinition(type=VariableType.FLOAT),
        "enabled": VariableDefinition(type=VariableType.BOOL),
    }

    resolved = resolver.resolve_all(
        definitions,
        global_values={"count": "42", "ratio": "3.5", "enabled": "true"},
    )

    assert resolved["count"] == 42
    assert resolved["ratio"] == 3.5
    assert resolved["enabled"] is True


def test_type_coercion_raises_for_invalid_cast() -> None:
    resolver = VariableResolver()

    with pytest.raises(VariableResolutionError):
        resolver.resolve_all(
            {"count": VariableDefinition(type=VariableType.INT)},
            global_values={"count": "not-a-number"},
        )


def test_constraint_validation_checks_choices_and_pattern() -> None:
    resolver = VariableResolver()
    definitions = {
        "python_version": VariableDefinition(
            type=VariableType.STR,
            choices=["3.11", "3.12"],
            pattern=r"^3\.\d{2}$",
        )
    }

    resolved = resolver.resolve_all(definitions, global_values={"python_version": "3.12"})
    assert resolved["python_version"] == "3.12"

    with pytest.raises(VariableResolutionError):
        resolver.resolve_all(definitions, global_values={"python_version": "3.09"})

    with pytest.raises(VariableResolutionError):
        resolver.resolve_all(
            {
                "project_name": VariableDefinition(
                    type=VariableType.STR,
                    pattern=r"^[a-z_]+$",
                )
            },
            global_values={"project_name": "My-Project"},
        )


def test_read_env_values_uses_prefix() -> None:
    resolver = VariableResolver()
    definitions = {
        "project_name": VariableDefinition(type=VariableType.STR),
        "port": VariableDefinition(type=VariableType.INT),
    }

    values = resolver.read_env_values(
        definitions,
        environ={"MIXY_VAR_PROJECT_NAME": "env-name", "OTHER": "ignored"},
    )

    assert values == {"project_name": "env-name"}


def test_load_vars_file_reads_yaml_mapping() -> None:
    loaded = load_vars_file(VARS_FIXTURE)

    assert loaded["project_name"] == "from-file"
    assert loaded["port"] == 9000


def test_build_source_context_merges_global_values_and_source_overrides() -> None:
    resolver = VariableResolver()
    definitions = {
        "project_name": VariableDefinition(type=VariableType.STR),
        "port": VariableDefinition(type=VariableType.INT),
    }

    context = resolver.build_source_context(
        definitions,
        resolved_global={"project_name": "global", "port": 8080},
        source_values={"port": "3000"},
    )

    assert context == {"project_name": "global", "port": 3000}


def test_prompting_resolves_missing_required_variable() -> None:
    prompts: list[tuple[str, bool]] = []

    def fake_prompt(text: str, *, hide_input: bool = False) -> str:
        prompts.append((text, hide_input))
        return "demo_project"

    resolver = VariableResolver(prompt_fn=fake_prompt)
    definitions = {
        "project_name": VariableDefinition(
            type=VariableType.STR,
            description="Project slug",
            choices=["demo_project", "sample_project"],
        )
    }

    resolved = resolver.resolve_all(definitions)

    assert resolved["project_name"] == "demo_project"
    assert "Project slug" in prompts[0][0]
    assert "choices: demo_project, sample_project" in prompts[0][0]


def test_non_interactive_mode_raises_for_missing_required_variable() -> None:
    resolver = VariableResolver()

    with pytest.raises(VariableResolutionError):
        resolver.resolve_all(
            {"project_name": VariableDefinition(type=VariableType.STR)},
            non_interactive=True,
        )


def test_secret_prompt_uses_hidden_input() -> None:
    prompts: list[tuple[str, bool]] = []

    def fake_prompt(text: str, *, hide_input: bool = False) -> str:
        prompts.append((text, hide_input))
        return "hunter2"

    resolver = VariableResolver(prompt_fn=fake_prompt)
    definitions = {"db_password": VariableDefinition(type=VariableType.STR, secret=True)}

    resolved = resolver.resolve_all(definitions)

    assert resolved["db_password"] == "hunter2"
    assert prompts[0][1] is True


def test_parse_cli_overrides_parses_key_value_pairs() -> None:
    resolver = VariableResolver()

    parsed = resolver.parse_cli_overrides(["project_name=demo", "port=3000"])

    assert parsed == {"project_name": "demo", "port": "3000"}


def test_parse_cli_overrides_rejects_invalid_input() -> None:
    resolver = VariableResolver()

    with pytest.raises(VariableResolutionError):
        resolver.parse_cli_overrides(["missing-separator"])


def test_secret_masking_replaces_secret_values_in_log_output() -> None:
    sink: list[str] = []
    handler_id = logger.add(sink.append, format="{message}")

    try:
        resolver = VariableResolver()
        definitions = {
            "db_password": VariableDefinition(type=VariableType.STR, secret=True),
            "project_name": VariableDefinition(type=VariableType.STR),
        }
        resolver.resolve_all(
            definitions,
            global_values={"db_password": "hunter2", "project_name": "mixy"},
        )

        logger.info("Resolved secret {}", "hunter2")
        logger.info("Resolved project {}", "mixy")
    finally:
        logger.remove(handler_id)
        logger.configure(patcher=None)

    joined = "\n".join(sink)
    assert "***" in joined
    assert "hunter2" not in joined
    assert "mixy" in joined
