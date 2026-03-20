import importlib
from types import SimpleNamespace
from unittest.mock import Mock

from mixy.application import composition as composition_module
from mixy.application.composition import (
    PlanningDependencies,
    build_app_settings,
    build_generation_executor,
    build_planning_dependencies,
    build_rendering_adapter,
)
from mixy.application.ports import PromptGateway, RenderingAdapter
from mixy.application.services import SourceResolver, TemplateRenderer, VariableResolutionService
from mixy.application.settings import AppSettings
from mixy.domain.enums import ConflictPolicy
from mixy.domain.models import OutputDefinition, ProjectDefinition, RenderPlan
from mixy.domain.services import MergePlanner
from mixy.infrastructure.filesystem.file_writer import GenerationExecutor

generate_module = importlib.import_module("mixy.application.use_cases.generate_project")
plan_module = importlib.import_module("mixy.application.use_cases.plan_project")


def test_build_planning_dependencies_assembles_default_runtime_components(
    monkeypatch,
) -> None:
    provider = object()
    monkeypatch.setattr(
        composition_module,
        "get_source_providers",
        lambda: [provider],
    )

    dependencies = build_planning_dependencies()

    assert isinstance(dependencies.variable_resolution_service, VariableResolutionService)
    assert isinstance(dependencies.source_resolver, SourceResolver)
    assert dependencies.source_resolver.list_providers() == [provider]
    assert isinstance(dependencies.template_renderer, TemplateRenderer)
    assert isinstance(dependencies.merge_planner, MergePlanner)


def test_build_generation_executor_preserves_provided_executor() -> None:
    executor = GenerationExecutor()

    assert build_generation_executor(executor) is executor
    assert isinstance(build_generation_executor(), GenerationExecutor)


def test_plan_project_uses_the_composed_merge_planner(monkeypatch, tmp_path) -> None:
    output_path = tmp_path / "output"
    definition = ProjectDefinition(
        version="1",
        sources=[],
        output=OutputDefinition(path=output_path, conflict_policy=ConflictPolicy.FAIL),
    )
    prepared = SimpleNamespace(
        definition=definition,
        materialized_sources=[],
        render_decisions={},
    )
    planned_plan = RenderPlan(
        operations=[],
        conflicts=[],
        conflict_policy=ConflictPolicy.FAIL,
        output_path=output_path,
    )
    build_plan = Mock(return_value=planned_plan)
    dependencies = PlanningDependencies(
        variable_resolution_service=VariableResolutionService(),
        source_resolver=SourceResolver([]),
        template_renderer=TemplateRenderer(),
        merge_planner=SimpleNamespace(build_plan=build_plan),
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        plan_module,
        "build_planning_dependencies",
        lambda **kwargs: dependencies,
    )

    def fake_prepare_project(*args, **kwargs):
        captured["planning_dependencies"] = kwargs["planning_dependencies"]
        return prepared

    monkeypatch.setattr(plan_module, "prepare_project", fake_prepare_project)

    result = plan_module.plan_project(tmp_path / "config.yml")

    assert result.plan is planned_plan
    assert captured["planning_dependencies"] is dependencies
    build_plan.assert_called_once_with([], definition.output, {})


def test_generate_project_uses_the_composed_generation_executor(monkeypatch, tmp_path) -> None:
    planned = SimpleNamespace(plan=SimpleNamespace(marker="plan"))
    execution_result = SimpleNamespace(marker="result")
    build_generation_executor_mock = Mock(
        return_value=SimpleNamespace(execute=Mock(return_value=execution_result))
    )

    monkeypatch.setattr(
        generate_module,
        "build_generation_executor",
        build_generation_executor_mock,
    )
    monkeypatch.setattr(generate_module, "plan_project", Mock(return_value=planned))

    result = generate_module.generate_project(tmp_path / "config.yml")

    assert result is execution_result
    build_generation_executor_mock.assert_called_once_with(None)
    generate_module.plan_project.assert_called_once()


class StubPromptGateway(PromptGateway):
    def prompt(self, text: str, *, hide_input: bool = False) -> str:
        return "ignored"


def test_build_planning_dependencies_preserves_provided_runtime_ports() -> None:
    config_loader = Mock()
    vars_file_loader = Mock()
    metadata_resolver_factory = Mock()
    prompt_gateway = StubPromptGateway()
    secret_masker = Mock()

    assert composition_module.build_config_loader(config_loader) is config_loader
    assert composition_module.build_vars_file_loader(vars_file_loader) is vars_file_loader
    assert (
        composition_module.build_metadata_resolver_factory(metadata_resolver_factory)
        is metadata_resolver_factory
    )
    assert composition_module.build_prompt_gateway(prompt_gateway) is prompt_gateway
    assert composition_module.build_secret_masker(secret_masker) is secret_masker


def test_build_source_provider_registry_preserves_provided_registry() -> None:
    provider = object()

    class StubRegistry:
        def list_providers(self) -> list[object]:
            return [provider]

    registry = StubRegistry()

    assert composition_module.build_source_provider_registry(registry) is registry
    assert registry.list_providers() == [provider]


def test_build_app_settings_reads_runtime_environment(monkeypatch) -> None:
    monkeypatch.setenv("MIXY_CACHE_ROOT", "/tmp/mixy-cache")
    monkeypatch.setenv("MIXY_ENABLED_SOURCE_PROVIDERS", "git,local_dir")

    settings = build_app_settings()

    assert settings == AppSettings(
        cache_root="/tmp/mixy-cache",
        enabled_source_providers=["git", "local_dir"],
    )


class StubRenderingAdapter(RenderingAdapter):
    def is_binary(self, source_path):
        return False

    def strip_jinja_suffix(self, name: str) -> str:
        return name

    def has_jinja_suffix(self, name: str) -> bool:
        return False

    def render_string(self, template: str, context: dict[str, object]) -> str:
        return template


def test_build_rendering_adapter_preserves_provided_adapter() -> None:
    adapter = StubRenderingAdapter()

    assert build_rendering_adapter(adapter) is adapter
    assert isinstance(build_rendering_adapter(), composition_module.DefaultRenderingAdapter)
