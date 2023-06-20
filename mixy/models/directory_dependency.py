from pathlib import Path
from typing import Iterator, Literal

import tomllib
from pydantic.types import DirectoryPath

from mixy.context import Context
from mixy.models.mixy_dependency import MixyDependency
from mixy.protocols.dependency import Dependency
from mixy.utils import get_directory_contents, join_local_path

from .base import RenderableBaseModel
from .file_dependency import FileDependency
from .template_var import TemplateVar


class DirectoryDependency(RenderableBaseModel):
    src_type: Literal["directory"] = "directory"
    src: DirectoryPath
    dest: Path = Path("/")
    ignores: list[str] = []

    @property
    def iter_dependencies(self) -> Iterator[Dependency]:
        dir_content = get_directory_contents(self.src, self.ignores)
        for x in dir_content:
            dest = Path("/").joinpath(x.relative_to(self.src))
            if x.is_dir() and x.name == ".mixy":
                continue
            elif x.is_dir():
                yield DirectoryDependency(src=x, dest=dest, ignores=self.ignores)
            elif x.suffix == ".mixy":
                yield MixyDependency(src=x, dest=dest)
            else:
                yield FileDependency(src=x, dest=dest)

    def _load_template_vars(self, vars_file: Path) -> dict[str, TemplateVar]:
        with open(vars_file, "rb") as f:
            data = tomllib.load(f)
        return {k: TemplateVar(**v) for k, v in data.items()}

    def resolve(self, into_dir: Path, context: Context) -> None:
        abs_dest = join_local_path(into_dir, self.dest)
        abs_dest.mkdir(exist_ok=True, parents=True)
        vars_file = self.src / ".mixy" / "vars.toml"
        if vars_file.exists():
            template_vars = self._load_template_vars(vars_file)
            context = Context.derive_from(context, **template_vars)

        for d in self.iter_dependencies:
            d.resolve(abs_dest, context)
