import pytest
from loguru import logger

from mixy.application.services import VariableResolutionService
from mixy.domain.enums import VariableType
from mixy.domain.exceptions import VariableResolutionError
from mixy.domain.models import VariableDefinition


class RecordingPromptGateway:
    def __init__(self, answers: list[str]) -> None:
        self._answers = iter(answers)
        self.calls: list[tuple[str, bool]] = []

    def prompt(self, text: str, *, hide_input: bool = False) -> str:
        self.calls.append((text, hide_input))
        return next(self._answers)


def test_variable_resolution_service_prompts_and_caches_answers() -> None:
    gateway = RecordingPromptGateway(["demo_project"])
    service = VariableResolutionService(prompt_gateway=gateway)
    definitions = {
        "project_name": VariableDefinition(
            type=VariableType.STR,
            description="Project slug",
            choices=["demo_project", "sample_project"],
        )
    }

    resolved = service.resolve_all(definitions)
    resolved_again = service.resolve_all(definitions)

    assert resolved["project_name"] == "demo_project"
    assert resolved_again["project_name"] == "demo_project"
    assert len(gateway.calls) == 1
    assert "Project slug" in gateway.calls[0][0]
    assert "choices: demo_project, sample_project" in gateway.calls[0][0]
    assert gateway.calls[0][1] is False


def test_variable_resolution_service_honors_non_interactive_mode() -> None:
    gateway = RecordingPromptGateway(["demo_project"])
    service = VariableResolutionService(prompt_gateway=gateway)

    with pytest.raises(VariableResolutionError):
        service.resolve_all(
            {"project_name": VariableDefinition(type=VariableType.STR)},
            non_interactive=True,
        )

    assert gateway.calls == []


def test_variable_resolution_service_masks_secret_values_in_logs() -> None:
    sink: list[str] = []
    handler_id = logger.add(sink.append, format="{message}")

    try:
        service = VariableResolutionService(prompt_gateway=RecordingPromptGateway(["hunter2"]))
        definitions = {
            "db_password": VariableDefinition(type=VariableType.STR, secret=True),
            "project_name": VariableDefinition(type=VariableType.STR),
        }

        resolved = service.resolve_all(
            definitions,
            global_values={"db_password": "hunter2", "project_name": "mixy"},
        )

        logger.info("Resolved secret {}", resolved["db_password"])
        logger.info("Resolved project {}", resolved["project_name"])
    finally:
        logger.remove(handler_id)
        logger.configure(patcher=None)

    joined = "\n".join(sink)
    assert "***" in joined
    assert "hunter2" not in joined
    assert "mixy" in joined


def test_variable_resolution_service_uses_injected_secret_masker() -> None:
    seen_masks: list[set[str]] = []

    def secret_masker(values) -> None:
        seen_masks.append(set(values))

    service = VariableResolutionService(
        prompt_gateway=RecordingPromptGateway(["hunter2"]),
        secret_masker=secret_masker,
    )
    definitions = {
        "db_password": VariableDefinition(type=VariableType.STR, secret=True),
        "project_name": VariableDefinition(type=VariableType.STR),
    }

    resolved = service.resolve_all(
        definitions,
        global_values={"db_password": "hunter2", "project_name": "mixy"},
    )

    assert resolved["db_password"] == "hunter2"
    assert seen_masks == [{"hunter2"}]
