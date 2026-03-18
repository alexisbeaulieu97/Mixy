"""Variable resolution with precedence, coercion, and validation."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

from pydantic import TypeAdapter, ValidationError

from mixy.domain.enums import VariableType
from mixy.domain.exceptions import VariableResolutionError
from mixy.domain.models import ScalarValue, VariableDefinition

ResolvedVariables = dict[str, ScalarValue]


TYPE_ADAPTERS: dict[VariableType, TypeAdapter[Any]] = {
    VariableType.STR: TypeAdapter(str),
    VariableType.INT: TypeAdapter(int),
    VariableType.FLOAT: TypeAdapter(float),
    VariableType.BOOL: TypeAdapter(bool),
}


@dataclass(frozen=True, slots=True)
class ResolutionContext:
    """All inputs needed to resolve a set of variable definitions."""

    definitions: Mapping[str, VariableDefinition]
    global_values: Mapping[str, object] = field(default_factory=dict)
    source_values: Mapping[str, object] = field(default_factory=dict)
    cli_overrides: Mapping[str, object] = field(default_factory=dict)
    vars_file_values: Mapping[str, object] = field(default_factory=dict)
    fallback_values: Mapping[str, object] = field(default_factory=dict)
    default_values: Mapping[str, object] = field(default_factory=dict)
    env_prefix: str = "MIXY_VAR_"
    environ: Mapping[str, str] | None = None


class VariableResolver:
    """Resolve variable values from layered sources into typed runtime data."""

    def resolve(self, context: ResolutionContext) -> ResolvedVariables:
        """Resolve one definition set using the configured precedence layers."""
        env_values = self.read_env_values(
            context.definitions,
            environ=context.environ,
            prefix=context.env_prefix,
        )
        resolved: ResolvedVariables = {}

        for name, definition in context.definitions.items():
            candidate: object | None = None

            if name in context.cli_overrides:
                candidate = context.cli_overrides[name]
            elif name in context.source_values:
                candidate = context.source_values[name]
            elif name in context.vars_file_values:
                candidate = context.vars_file_values[name]
            elif name in env_values:
                candidate = env_values[name]
            elif name in context.global_values:
                candidate = context.global_values[name]
            elif name in context.default_values:
                candidate = context.default_values[name]
            elif name in context.fallback_values:
                candidate = context.fallback_values[name]
            else:
                candidate = definition.default

            if candidate is None:
                if not definition.required:
                    continue
                raise VariableResolutionError(
                    name,
                    None,
                    "Required variable is unresolved.",
                    suggestion=(
                        "Provide the value via `--var`, `--vars-file`, environment, "
                        "or template defaults."
                    ),
                )

            resolved[name] = self._coerce_and_validate(name, definition, candidate)

        return resolved

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
    ) -> ResolvedVariables:
        return self.resolve(
            ResolutionContext(
                definitions=definitions,
                global_values=global_values or {},
                source_values=source_values or {},
                cli_overrides=cli_overrides or {},
                vars_file_values=vars_file_values or {},
                fallback_values=fallback_values or {},
                env_prefix=env_prefix,
                environ=environ,
            )
        )

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
        fallback_values: Mapping[str, object] | None = None,
        env_prefix: str = "MIXY_VAR_",
        environ: Mapping[str, str] | None = None,
    ) -> ResolvedVariables:
        result = self.resolve(
            ResolutionContext(
                definitions=definitions,
                global_values=dict(resolved_global) | dict(global_values or {}),
                source_values=source_values or {},
                cli_overrides=cli_overrides or {},
                vars_file_values=vars_file_values or {},
                fallback_values=fallback_values or {},
                default_values=default_values or {},
                env_prefix=env_prefix,
                environ=environ,
            )
        )
        return result

    def read_env_values(
        self,
        definitions: Mapping[str, VariableDefinition],
        *,
        environ: Mapping[str, str] | None = None,
        prefix: str = "MIXY_VAR_",
    ) -> dict[str, str]:
        source: Mapping[str, str] = environ if environ is not None else os.environ
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
