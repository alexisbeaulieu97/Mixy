from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from jinja2 import Environment
from pydantic import Field

from mixy.cached_vars_manager import CachedVarsManager
from mixy.models.base import BaseModel
from mixy.models.template_var import TemplateVar
from mixy.plugins.plugin_manager import plugin_master

if TYPE_CHECKING:
    from mixy.models.field_types import AbsolutePath
    from mixy.models.template import Template


class Blueprint(BaseModel):
    global_scope: Optional[CachedVarsManager] = Field(None)
    scopes: dict[AbsolutePath, CachedVarsManager] = Field({})
    templates: list[Template] = Field([])

    def add_scope(
        self,
        scope_path: AbsolutePath,
        scope_vars: dict[str, TemplateVar],
    ) -> None:
        scope = CachedVarsManager(vars=scope_vars)
        self.scopes[scope_path] = scope

    def add_template(
        self,
        template: Template,
    ) -> None:
        self.templates.append(template)

    def build(
        self,
        destination: Path,
        env: Environment,
    ) -> None:
        for template in self.templates:
            vars_managers = self._get_variable_managers(template)
            resolved_vars = self._resolve_variables(template, vars_managers)

            abs_dest = self._get_template_destination(
                destination,
                template,
                resolved_vars,
                env,
            )

            self._write_template_content(
                abs_dest,
                template,
                resolved_vars,
                env,
            )

    def _write_template_content(
        self,
        destination: Path,
        template: Template,
        resolved_vars: dict[str, Any],
        env: Environment,
    ) -> None:
        content = template.content
        if isinstance(template.content, str):
            content = self._render(
                template.content,
                resolved_vars,
                env,
            )
        plugin_master.hook.output(destination=destination, content=content)

    def _get_template_destination(
        self,
        destination: Path,
        template: Template,
        resolved_vars: dict[str, Any],
        env: Environment,
    ) -> Path:
        template_dest = destination.joinpath(template.destination.relative_to("/"))
        template_dest = Path(self._render(str(template_dest), resolved_vars, env))
        template_dest.parent.mkdir(parents=True, exist_ok=True)
        return template_dest

    def _render(
        self,
        template_string: str,
        vars: dict[str, Any],
        env: Environment,
    ) -> str:
        return env.from_string(template_string).render(**vars)

    def _resolve_variables(
        self, template: Template, vars_managers: list[CachedVarsManager]
    ) -> dict[str, Any]:
        """Resolve the template variables using the provided variable managers."""
        resolved_vars = {}
        var_names = self._get_variable_names(vars_managers)
        for var_name in var_names:
            for vars_manager in vars_managers:
                if vars_manager.has_var(var_name):
                    resolved_vars[var_name] = vars_manager.get_value(var_name)
                    break
        return resolved_vars

    def _get_variable_names(
        self,
        vars_managers: list[CachedVarsManager],
    ) -> set[str]:
        """Return the names of all variables in the provided variable managers."""
        vars_names: set[str] = set()
        for vars_manager in vars_managers:
            vars_names.update(vars_manager.get_vars_names())
        return vars_names

    def _get_variable_managers(
        self,
        template: Template,
    ) -> list[CachedVarsManager]:
        """Return the variable managers for the provided template."""
        vars_managers: list[CachedVarsManager] = (
            [self.global_scope] if self.global_scope is not None else []
        )
        scope_path = Path("/")
        for part in template.destination.parts:
            scope_path = scope_path / part
            if scope_path in self.scopes:
                vars_managers.insert(0, self.scopes[scope_path])
        return vars_managers


# we need a way for plugins to add variables relative to a path in the blueprint
# we will then parse the variables at the end and create a scope
# we need a way to store variables which have already been resolved
# this means we should probably split paths and store each part recursively in a dict

# we need to consider making a DependencyBlueprint
# this means each dependency could have its own variable blueprint
# plugins can add scopes and templates whilst fetching and parsing dependencies
# this means we will retrieve a blueprint for each dependency, and we can call
# the build method from the projectbuilder on each blueprint

# we need to consider ProjectBlueprint
# this means variable scopes can be overwritten
# we need to consider the potential problems on windows paths (uppercase = lowercase)
# is not the same thing as Linux paths (uppercase != lowercase)

# we also need to consider the fact that there may be some variables in paths
# and they may have some weird stuff in them like {@ some_path | upper @}

# after some thought, i think each dependency needs to have its own blueprint
# this is because some file/directory names contain variables and when replaced
# they might not end up being the same when we consider the scoped context
# even though they may share the same variable name

# we should consider making a projectblueprint out of a list of dependencyblueprint
# or drop the entire idea of project/dependency blueprint and make a single blueprint
