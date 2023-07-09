from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment
from pydantic import Field

from mixy.models.base import BaseModel

if TYPE_CHECKING:
    from mixy.models.field_types import AbsolutePath
    from mixy.models.template import Template
    from mixy.vars_manager import VarsManager


class Blueprint(BaseModel):
    scopes: dict[AbsolutePath, VarsManager] = Field({})
    templates: list[Template] = Field([])

    def add_scope(
        self,
        scope_path: AbsolutePath,
        scope: VarsManager,
    ) -> None:
        self.scopes[scope_path] = scope

    def add_template(
        self,
        template: Template,
    ) -> None:
        self.templates.append(template)

    def get_vars_managers_for_template(
        self,
        template: Template,
    ) -> list[VarsManager]:
        vars_managers: list[VarsManager] = []
        scope_path = Path("/")
        for part in template.destination.parts:
            scope_path = scope_path / part
            if scope_path in self.scopes:
                vars_managers.insert(0, self.scopes[scope_path])
        return vars_managers

    def get_vars_names_for_template(
        self,
        template: Template,
    ) -> set[str]:
        vars_names: set[str] = set()
        for vars_manager in self.get_vars_managers_for_template(template):
            vars_names.update(vars_manager.get_vars_names())
        return vars_names

    def build(self, destination: Path, environment: Environment) -> None:
        for template in self.templates:
            vars_managers = self.get_vars_managers_for_template(template)
            resolved_vars = {}
            for var_name in self.get_vars_names_for_template(template):
                for vars_manager in vars_managers:
                    if vars_manager.has_var(var_name):
                        resolved_vars[var_name] = vars_manager.get_value(var_name)
                        break

            abs_dest = destination.joinpath(template.destination.relative_to("/"))
            abs_dest = Path(
                environment.from_string(str(abs_dest)).render(**resolved_vars)
            )
            abs_dest.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(template.content, bytes):
                abs_dest.write_bytes(template.content)
            else:
                jinja_template = environment.from_string(template.content)
                rendered_content = jinja_template.render(**resolved_vars)
                abs_dest.write_text(rendered_content)


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
