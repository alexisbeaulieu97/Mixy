"""Application-owned variable resolution orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from mixy.application.composition import build_prompt_gateway, build_secret_masker
from mixy.application.ports import PromptGateway, SecretMasker
from mixy.domain.exceptions import VariableResolutionError
from mixy.domain.models import ScalarValue, VariableDefinition
from mixy.domain.services.variable_resolver import ResolutionContext, VariableResolver


class VariableResolutionService:
    """Resolve variables while owning prompting and secret masking concerns."""

    def __init__(
        self,
        *,
        variable_resolver: VariableResolver | None = None,
        prompt_gateway: PromptGateway | None = None,
        secret_masker: SecretMasker | None = None,
    ) -> None:
        self._resolver = variable_resolver or VariableResolver()
        self._prompt_gateway = build_prompt_gateway(prompt_gateway)
        self._secret_masker = build_secret_masker(secret_masker)
        self._prompt_cache: dict[str, object] = {}
        self._secret_values: set[str] = set()

    def resolve_all(
        self,
        definitions: Mapping[str, VariableDefinition],
        global_values: Mapping[str, object] | None = None,
        source_values: Mapping[str, object] | None = None,
        cli_overrides: Mapping[str, object] | None = None,
        env_prefix: str = "MIXY_VAR_",
        *,
        vars_file_values: Mapping[str, object] | None = None,
        fallback_values: Mapping[str, object] | None = None,
        environ: Mapping[str, str] | None = None,
        non_interactive: bool = False,
    ) -> dict[str, ScalarValue]:
        context = ResolutionContext(
            definitions=definitions,
            global_values=global_values or {},
            source_values=source_values or {},
            cli_overrides=cli_overrides or {},
            vars_file_values=vars_file_values or {},
            fallback_values=fallback_values or {},
            env_prefix=env_prefix,
            environ=environ,
        )
        return self._resolve_with_prompt(context, allow_prompt=not non_interactive)

    def build_source_context(
        self,
        definitions: Mapping[str, VariableDefinition],
        resolved_global: Mapping[str, ScalarValue],
        source_values: Mapping[str, object] | None = None,
        cli_overrides: Mapping[str, object] | None = None,
    ) -> dict[str, ScalarValue]:
        context = self._resolver.build_source_context(
            definitions,
            resolved_global,
            source_values=source_values,
            cli_overrides=cli_overrides,
        )
        self._record_secret_values(context, definitions)
        return context

    def build_effective_context(
        self,
        definitions: Mapping[str, VariableDefinition],
        resolved_global: Mapping[str, ScalarValue],
        *,
        global_values: Mapping[str, object] | None = None,
        vars_file_values: Mapping[str, object] | None = None,
        source_values: Mapping[str, object] | None = None,
        cli_overrides: Mapping[str, object] | None = None,
        default_values: Mapping[str, object] | None = None,
        fallback_values: Mapping[str, object] | None = None,
        env_prefix: str = "MIXY_VAR_",
        environ: Mapping[str, str] | None = None,
        non_interactive: bool = False,
    ) -> dict[str, ScalarValue]:
        context = ResolutionContext(
            definitions=definitions,
            global_values=dict(resolved_global) | dict(global_values or {}),
            source_values=source_values or {},
            cli_overrides=cli_overrides or {},
            vars_file_values=vars_file_values or {},
            fallback_values={**self._prompt_cache, **(fallback_values or {})},
            default_values=default_values or {},
            env_prefix=env_prefix,
            environ=environ,
        )
        return self._resolve_with_prompt(context, allow_prompt=not non_interactive)

    def read_env_values(
        self,
        definitions: Mapping[str, VariableDefinition],
        *,
        environ: Mapping[str, str] | None = None,
        prefix: str = "MIXY_VAR_",
    ) -> dict[str, str]:
        return self._resolver.read_env_values(definitions, environ=environ, prefix=prefix)

    def parse_cli_overrides(self, overrides: Sequence[str]) -> dict[str, str]:
        return self._resolver.parse_cli_overrides(overrides)

    def _resolve_with_prompt(
        self,
        context: ResolutionContext,
        *,
        allow_prompt: bool,
    ) -> dict[str, ScalarValue]:
        merged_fallback = dict(self._prompt_cache) | dict(context.fallback_values)

        while True:
            active_context = ResolutionContext(
                definitions=context.definitions,
                global_values=context.global_values,
                source_values=context.source_values,
                cli_overrides=context.cli_overrides,
                vars_file_values=context.vars_file_values,
                fallback_values=merged_fallback,
                default_values=context.default_values,
                env_prefix=context.env_prefix,
                environ=context.environ,
            )

            try:
                resolved = self._resolver.resolve(active_context)
            except VariableResolutionError as error:
                if not allow_prompt or error.reason != "Required variable is unresolved.":
                    raise

                if error.variable_name not in context.definitions:
                    raise

                definition = context.definitions[error.variable_name]
                raw_value = self._prompt_gateway.prompt(
                    self._build_prompt_text(error.variable_name, definition),
                    hide_input=definition.secret,
                )
                merged_fallback[error.variable_name] = cast(object, raw_value)
                continue

            self._prompt_cache.update(merged_fallback)
            self._record_secret_values(resolved, context.definitions)
            return resolved

    def _record_secret_values(
        self,
        resolved: Mapping[str, ScalarValue],
        definitions: Mapping[str, VariableDefinition],
    ) -> None:
        self._secret_values.update(
            str(resolved[name])
            for name, definition in definitions.items()
            if definition.secret and name in resolved
        )
        self._secret_masker(self._secret_values)

    def _build_prompt_text(self, name: str, definition: VariableDefinition) -> str:
        parts = [name]
        if definition.description:
            parts.append(definition.description)
        if definition.choices:
            choices = ", ".join(str(choice) for choice in definition.choices)
            parts.append(f"choices: {choices}")
        return " - ".join(parts)
