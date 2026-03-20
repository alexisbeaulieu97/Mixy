"""Application-owned variable resolution orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Dict, Optional, cast

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
        global_values: Optional[Mapping[str, object]] = None,
        source_values: Optional[Mapping[str, object]] = None,
        cli_overrides: Optional[Mapping[str, object]] = None,
        env_prefix: str = "MIXY_VAR_",
        *,
        vars_file_values: Optional[Mapping[str, object]] = None,
        fallback_values: Optional[Mapping[str, object]] = None,
        environ: Optional[Mapping[str, str]] = None,
        non_interactive: bool = False,
    ) -> Dict[str, ScalarValue]:
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
        source_values: Optional[Mapping[str, object]] = None,
        cli_overrides: Optional[Mapping[str, object]] = None,
    ) -> Dict[str, ScalarValue]:
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
        global_values: Optional[Mapping[str, object]] = None,
        vars_file_values: Optional[Mapping[str, object]] = None,
        source_values: Optional[Mapping[str, object]] = None,
        cli_overrides: Optional[Mapping[str, object]] = None,
        default_values: Optional[Mapping[str, object]] = None,
        fallback_values: Optional[Mapping[str, object]] = None,
        env_prefix: str = "MIXY_VAR_",
        environ: Optional[Mapping[str, str]] = None,
        non_interactive: bool = False,
    ) -> Dict[str, ScalarValue]:
        context = ResolutionContext(
            definitions=definitions,
            global_values=_merge_mappings(resolved_global, global_values),
            source_values=source_values or {},
            cli_overrides=cli_overrides or {},
            vars_file_values=vars_file_values or {},
            fallback_values=_merge_mappings(self._prompt_cache, fallback_values),
            default_values=default_values or {},
            env_prefix=env_prefix,
            environ=environ,
        )
        return self._resolve_with_prompt(context, allow_prompt=not non_interactive)

    def read_env_values(
        self,
        definitions: Mapping[str, VariableDefinition],
        *,
        environ: Optional[Mapping[str, str]] = None,
        prefix: str = "MIXY_VAR_",
    ) -> Dict[str, str]:
        return self._resolver.read_env_values(definitions, environ=environ, prefix=prefix)

    def parse_cli_overrides(self, overrides: Sequence[str]) -> Dict[str, str]:
        return self._resolver.parse_cli_overrides(overrides)

    def _resolve_with_prompt(
        self,
        context: ResolutionContext,
        *,
        allow_prompt: bool,
    ) -> Dict[str, ScalarValue]:
        merged_fallback = _merge_mappings(self._prompt_cache, context.fallback_values)

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


def _merge_mappings(
    primary: Mapping[str, object],
    secondary: Optional[Mapping[str, object]],
) -> Dict[str, object]:
    merged = dict(primary)
    merged.update(secondary or {})
    return merged
