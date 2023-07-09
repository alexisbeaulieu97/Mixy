from pathlib import Path

from mixy.models.base import BaseModel
from mixy.models.blueprint import Blueprint
from mixy.models.source_meta import SourceMeta
from mixy.models.template_var import TemplateVar
from mixy.plugins.plugin_manager import plugin_master
from mixy.settings.project_settings import ProjectSettings


class Project(BaseModel):
    _RENDERABLE_EXCLUDES = {"settings", "vars"}

    dependencies: list[SourceMeta]
    destination: Path

    settings: ProjectSettings = ProjectSettings()
    vars: dict[str, TemplateVar] = {}

    def create(self) -> list[Blueprint]:
        blueprints = []
        for dependency in self.dependencies:
            blueprint = Blueprint()
            plugin_master.hook.fetch(
                source=dependency,
                blueprint=blueprint,
            )
            blueprints.append(blueprint)
        return blueprints
        # for dependency in dependency_list:
        #     parser = parser_class(**dependency)
        #     for handler in parser.parse(context):
        #         handler.handle(self.destination)
