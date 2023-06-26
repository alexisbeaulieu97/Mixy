from typing import Any
from pathlib import Path


from mixy.context import Context
from mixy.models.base import RenderableBaseModel
from mixy.models.template_var import TemplateVar
from mixy.plugins.plugin_capability import PluginCapability
from mixy.settings.project_settings import ProjectSettings
from mixy.utils import clear_directory
from mixy.plugins.plugin_loader import plugin_loader


class Project(RenderableBaseModel):
    _RENDERABLE_EXCLUDES = {"settings", "vars"}

    dependencies: dict[str, list[dict[str, Any]]]
    destination: Path

    settings: ProjectSettings = ProjectSettings()
    vars: dict[str, TemplateVar] = {}

    @property
    def exists(self) -> bool:
        return self.destination.exists()

    @property
    def is_empty(self) -> bool:
        if not self.exists:
            return True
        return not any(self.destination.iterdir())

    def create(self, context: Context) -> None:
        context = Context.derive_from(context, **self.vars)
        # self.render(context)
        self.destination.mkdir(exist_ok=True)
        for plugin_name, dependency_list in self.dependencies.items():
            parser_class = plugin_loader.search_best_plugins(
                "parser",
                PluginCapability(name="type", value="directory"),
                PluginCapability(name="file_type", value=".mixy"),
            )
            print(parser_class)
            # for dependency in dependency_list:
            #     parser = parser_class(**dependency)
            #     for handler in parser.parse(context):
            #         handler.handle(self.destination)

    def empty(self) -> None:
        if self.exists:
            clear_directory(self.destination)
