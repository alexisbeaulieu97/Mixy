"""Explicit application composition for planning and generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mixy.application.ports import (
    ConfigLoader,
    MetadataResolverFactory,
    PromptGateway,
    RenderingAdapter,
    RenderingAdapterError,
    SecretMasker,
    SourceProvider,
    SourceProviderRegistry,
    VarsFileLoader,
)
from mixy.domain.services import MergePlanner
from mixy.domain.services import MetadataResolver
from mixy.domain.services.variable_resolver import VariableResolver as DomainVariableResolver
from mixy.infrastructure.config import MetadataLoader, load_config, load_vars_file
from mixy.infrastructure.filesystem.file_writer import GenerationExecutor
from mixy.infrastructure.logging import configure_secret_masking
from mixy.infrastructure.prompting import TyperPromptGateway
from mixy.infrastructure.rendering.binary_detection import is_binary
from mixy.infrastructure.rendering.jinja_renderer import (
    UndefinedVariableError,
    has_jinja_suffix,
    render_string,
    strip_jinja_suffix,
)
from mixy.plugins.manager import get_source_providers
from jinja2 import TemplateError


@dataclass(frozen=True, slots=True)
class PlanningDependencies:
    variable_resolution_service: VariableResolutionService
    source_resolver: SourceResolver
    template_renderer: TemplateRenderer
    merge_planner: MergePlanner


@dataclass(frozen=True, slots=True)
class EntryPointSourceProviderRegistry:
    """Default provider registry backed by pluggy entrypoint discovery."""

    def list_providers(self) -> list[SourceProvider]:
        return list(get_source_providers())


@dataclass(frozen=True, slots=True)
class DefaultRenderingAdapter:
    """Default rendering adapter backed by infrastructure Jinja helpers."""

    def is_binary(self, source_path: Path) -> bool:
        return is_binary(source_path)

    def strip_jinja_suffix(self, name: str) -> str:
        return strip_jinja_suffix(name)

    def has_jinja_suffix(self, name: str) -> bool:
        return has_jinja_suffix(name)

    def render_string(self, template: str, context: dict[str, object]) -> str:
        try:
            return render_string(template, context)
        except UndefinedVariableError as error:
            raise RenderingAdapterError(str(error), variable_name=error.name) from error
        except TemplateError as error:
            raise RenderingAdapterError(str(error)) from error


def build_planning_dependencies(
    *,
    variable_resolver: VariableResolutionService | DomainVariableResolver | None = None,
    source_resolver: SourceResolver | None = None,
    source_provider_registry: SourceProviderRegistry | None = None,
    template_renderer: TemplateRenderer | None = None,
    merge_planner: MergePlanner | None = None,
    prompt_gateway: PromptGateway | None = None,
    secret_masker: SecretMasker | None = None,
) -> PlanningDependencies:
    from mixy.application.services import SourceResolver, TemplateRenderer

    return PlanningDependencies(
        variable_resolution_service=_coerce_variable_resolution_service(
            variable_resolver,
            prompt_gateway=prompt_gateway,
            secret_masker=secret_masker,
        ),
        source_resolver=source_resolver
        or SourceResolver(build_source_provider_registry(source_provider_registry).list_providers()),
        template_renderer=template_renderer or TemplateRenderer(),
        merge_planner=merge_planner or MergePlanner(),
    )


def build_config_loader(config_loader: ConfigLoader | None = None) -> ConfigLoader:
    return config_loader or load_config


def build_vars_file_loader(vars_file_loader: VarsFileLoader | None = None) -> VarsFileLoader:
    return vars_file_loader or load_vars_file


def build_metadata_resolver_factory(
    metadata_resolver_factory: MetadataResolverFactory | None = None,
) -> MetadataResolverFactory:
    if metadata_resolver_factory is not None:
        return metadata_resolver_factory

    metadata_loader = MetadataLoader()

    def resolve(root_path: Path) -> MetadataResolver:
        discovered = metadata_loader.discover(root_path)
        return MetadataResolver(
            directory_scopes=discovered.directory_scopes,
            file_scopes=discovered.file_scopes,
        )

    return resolve


def build_source_provider_registry(
    source_provider_registry: SourceProviderRegistry | None = None,
) -> SourceProviderRegistry:
    return source_provider_registry or EntryPointSourceProviderRegistry()


def build_prompt_gateway(prompt_gateway: PromptGateway | None = None) -> PromptGateway:
    return prompt_gateway or TyperPromptGateway()


def build_secret_masker(secret_masker: SecretMasker | None = None) -> SecretMasker:
    return secret_masker or configure_secret_masking


def build_rendering_adapter(rendering_adapter: RenderingAdapter | None = None) -> RenderingAdapter:
    return rendering_adapter or DefaultRenderingAdapter()


def build_generation_executor(executor: GenerationExecutor | None = None) -> GenerationExecutor:
    return executor or GenerationExecutor()


def _coerce_variable_resolution_service(
    variable_resolver: VariableResolutionService | DomainVariableResolver | None,
    *,
    prompt_gateway: PromptGateway | None = None,
    secret_masker: SecretMasker | None = None,
) -> VariableResolutionService:
    from mixy.application.services import VariableResolutionService

    if isinstance(variable_resolver, VariableResolutionService):
        return variable_resolver
    return VariableResolutionService(
        variable_resolver=variable_resolver,
        prompt_gateway=build_prompt_gateway(prompt_gateway),
        secret_masker=build_secret_masker(secret_masker),
    )
