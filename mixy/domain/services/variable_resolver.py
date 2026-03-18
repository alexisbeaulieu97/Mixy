"""Variable resolution with precedence, coercion, prompting, and secret masking."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, cast

import typer
from loguru import logger
from pydantic import TypeAdapter, ValidationError

from mixy.domain.enums import VariableType
from mixy.domain.exceptions import VariableResolutionError
from mixy.domain.models import ScalarValue, VariableDefinition

ResolvedVariables = dict[str, ScalarValue]


class PromptFn(Protocol):
    def __call__(self, text: str, *, hide_input: bool = False) -> str: ...


TYPE_ADAPTERS: dict[VariableType, TypeAdapter[Any]] = {
    VariableType.STR: TypeAdapter(str),
    VariableType.INT: TypeAdapter(int),
    VariableType.FLOAT: TypeAdapter(float),
    VariableType.BOOL: TypeAdapter(bool),
}


class VariableResolver:
    """Resolve variable values from layered sources into typed runtime data."""

    def __init__(self, prompt_fn: PromptFn | None = None) -> None:
        self._prompt_fn = prompt_fn or cast(PromptFn, typer.prompt)
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
        environ: Mapping[str, str] | None = None,
        non_interactive: bool = False,
    ) -> ResolvedVariables:
        env_values = self.read_env_values(definitions, environ=environ, prefix=env_prefix)
        resolved: ResolvedVariables = {}

        for name, definition in definitions.items():
            candidate = self._select_candidate(
                name=name,
                definition=definition,
                global_values=global_values or {},
                env_values=env_values,
                vars_file_values=vars_file_values or {},
                source_values=source_values or {},
                cli_overrides=cli_overrides or {},
            )

            if candidate is None:
                continue

            resolved[name] = self._coerce_and_validate(name, definition, candidate)

        missing_required = [
            name
            for name, definition in definitions.items()
            if definition.required and name not in resolved
        ]
        if missing_required:
            if non_interactive:
                missing_display = ", ".join(sorted(missing_required))
                raise VariableResolutionError(
                    missing_display,
                    None,
                    "Required variables are unresolved in non-interactive mode.",
                    suggestion=(
                        "Provide required values via `--var`, `--vars-file`, or config defaults."
                    ),
                )

            prompted = self._prompt_for_missing(definitions, missing_required)
            for name, raw_value in prompted.items():
                resolved[name] = self._coerce_and_validate(name, definitions[name], raw_value)

        self.register_secret_masking(resolved, definitions)
        return resolved

    def build_source_context(
        self,
        definitions: Mapping[str, VariableDefinition],
        resolved_global: Mapping[str, ScalarValue],
        source_values: Mapping[str, object] | None = None,
        cli_overrides: Mapping[str, object] | None = None,
    ) -> ResolvedVariables:
        merged = dict(resolved_global)
        overrides = dict(source_values or {})
        overrides.update(cli_overrides or {})

        for name, raw_value in overrides.items():
            if name not in definitions:
                continue
            merged[name] = self._coerce_and_validate(name, definitions[name], raw_value)

        return merged

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
        env_prefix: str = "MIXY_VAR_",
        environ: Mapping[str, str] | None = None,
        non_interactive: bool = False,
        prompt_cache: dict[str, ScalarValue] | None = None,
    ) -> ResolvedVariables:
        env_values = self.read_env_values(definitions, environ=environ, prefix=env_prefix)
        resolved: ResolvedVariables = dict(resolved_global)
        prompted_values = dict(prompt_cache or {})

        for name, definition in definitions.items():
            candidate = self._select_candidate(
                name=name,
                definition=definition,
                global_values=global_values or {},
                env_values=env_values,
                vars_file_values=vars_file_values or {},
                source_values=source_values or {},
                cli_overrides=cli_overrides or {},
            )

            if candidate is None and name in resolved_global:
                candidate = resolved_global[name]
            if candidate is None and name in (default_values or {}):
                candidate = (default_values or {})[name]
            if candidate is None and name in prompted_values:
                candidate = prompted_values[name]
            if candidate is None:
                candidate = definition.default

            if candidate is None:
                if not definition.required:
                    continue
                if non_interactive:
                    raise VariableResolutionError(
                        name,
                        None,
                        "Required variable is unresolved in non-interactive mode.",
                        suggestion=(
                            "Provide the value via `--var`, `--vars-file`, environment, "
                            "or template defaults."
                        ),
                    )
                candidate = self._prompt_for_missing(definitions, [name])[name]
                validated = self._coerce_and_validate(name, definition, candidate)
                if prompt_cache is not None:
                    prompt_cache[name] = validated
                prompted_values[name] = validated

            resolved[name] = self._coerce_and_validate(name, definition, candidate)

        self.register_secret_masking(resolved, definitions)
        return resolved

    def read_env_values(
        self,
        definitions: Mapping[str, VariableDefinition],
        *,
        environ: Mapping[str, str] | None = None,
        prefix: str = "MIXY_VAR_",
    ) -> dict[str, str]:
        source = environ if environ is not None else {}
        if environ is None:
            source = os.environ
        values: dict[str, str] = {}

        for name in definitions:
            env_key = f"{prefix}{name.upper()}"
            if env_key in source:
                values[name] = source[env_key]

        return values

    def parse_cli_overrides(self, overrides: Sequence[str]) -> dict[str, str]:
        parsed: dict[str, str] = {}

        for item in overrides:
            if "=" not in item:
                raise VariableResolutionError(
                    item,
                    item,
                    "CLI overrides must use KEY=VALUE format.",
                    suggestion="Repeat `--var` as `--var name=value`.",
                )
            key, value = item.split("=", 1)
            if not key:
                raise VariableResolutionError(
                    item,
                    item,
                    "CLI override key cannot be empty.",
                    suggestion="Use `--var name=value` with a non-empty variable name.",
                )
            parsed[key] = value

        return parsed

    def register_secret_masking(
        self,
        resolved: Mapping[str, ScalarValue],
        definitions: Mapping[str, VariableDefinition],
    ) -> None:
        self._secret_values.update(
            str(resolved[name])
            for name, definition in definitions.items()
            if definition.secret and name in resolved
        )

        def patch_log_record(record: dict[str, Any]) -> None:
            message = record["message"]
            for secret in self._secret_values:
                if secret:
                    message = message.replace(secret, "***")
            record["message"] = message

        logger.configure(patcher=cast(Any, patch_log_record))

    def _select_candidate(
        self,
        *,
        name: str,
        definition: VariableDefinition,
        global_values: Mapping[str, object],
        env_values: Mapping[str, object],
        vars_file_values: Mapping[str, object],
        source_values: Mapping[str, object],
        cli_overrides: Mapping[str, object],
    ) -> object | None:
        if name in cli_overrides:
            return cli_overrides[name]
        if name in source_values:
            return source_values[name]
        if name in vars_file_values:
            return vars_file_values[name]
        if name in env_values:
            return env_values[name]
        if name in global_values:
            return global_values[name]
        return definition.default

    def _prompt_for_missing(
        self,
        definitions: Mapping[str, VariableDefinition],
        missing_required: Sequence[str],
    ) -> dict[str, str]:
        prompted: dict[str, str] = {}

        for name in missing_required:
            definition = definitions[name]
            prompt_text = self._build_prompt_text(name, definition)
            prompted[name] = self._prompt_fn(prompt_text, hide_input=definition.secret)

        return prompted

    def _build_prompt_text(self, name: str, definition: VariableDefinition) -> str:
        parts = [name]
        if definition.description:
            parts.append(definition.description)
        if definition.choices:
            choices = ", ".join(str(choice) for choice in definition.choices)
            parts.append(f"choices: {choices}")
        return " - ".join(parts)

    def _coerce_and_validate(
        self,
        name: str,
        definition: VariableDefinition,
        value: object,
    ) -> ScalarValue:
        adapter = TYPE_ADAPTERS[definition.type]

        try:
            coerced = cast(ScalarValue, adapter.validate_python(value))
        except ValidationError as error:
            raise VariableResolutionError(
                name,
                value,
                str(error.errors()[0]["msg"]),
                suggestion="Provide a value that matches the declared variable type.",
            ) from error

        if definition.choices is not None and coerced not in definition.choices:
            raise VariableResolutionError(
                name,
                value,
                f"Value must be one of: {', '.join(str(choice) for choice in definition.choices)}.",
                suggestion="Choose one of the declared variable choices.",
            )

        if definition.pattern is not None:
            string_value = str(coerced)
            if re.fullmatch(definition.pattern, string_value) is None:
                raise VariableResolutionError(
                    name,
                    value,
                    f'Value must match pattern "{definition.pattern}".',
                    suggestion="Provide a value that matches the configured pattern.",
                )

        return coerced
