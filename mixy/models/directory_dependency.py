from copy import deepcopy
from pathlib import Path
from typing import Iterator, Literal

import tomllib
from pydantic.types import DirectoryPath

from mixy.context import Context
from mixy.protocols.dependency import Dependency
from mixy.utils import get_directory_contents, join_local_path

from .base import RenderableBaseModel
from .file_dependency import FileDependency
from .vars_file import VarsFile


class DirectoryDependency(RenderableBaseModel):
    src_type: Literal["directory"] = "directory"
    src: DirectoryPath
    dest: Path = Path("/")
    ignores: list[str] = [".mixy"]

    @property
    def iter_dependencies(self) -> Iterator[Dependency]:
        dir_content = get_directory_contents(self.src, self.ignores)
        for x in dir_content:
            dest = Path("/").joinpath(x.relative_to(self.src))
            if x.is_dir():
                yield DirectoryDependency(src=x, dest=dest, ignores=self.ignores)
            else:
                yield FileDependency(src=x, dest=dest)

    def resolve(self, into_dir: Path, context: Context) -> None:
        abs_dest = join_local_path(into_dir, self.dest)
        abs_dest.mkdir(exist_ok=True, parents=True)
        _context = deepcopy(context)
        vars_file = self.src / ".mixy" / "vars.toml"
        if vars_file.exists():
            with open(vars_file, "rb") as f:
                data = tomllib.load(f)
            mixy_vars = VarsFile(**data)
            _context.update(**mixy_vars.variables)

        for d in self.iter_dependencies:
            d.resolve(abs_dest, _context)
