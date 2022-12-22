from pathlib import Path
from typing import Iterator, Literal

from pydantic.types import DirectoryPath

from supertemplater.context import Context
from supertemplater.protocols.dependency import Dependency
from supertemplater.utils import get_directory_contents, join_local_path

from .base import RenderableBaseModel
from .file_dependency import FileDependency


class DirectoryDependency(RenderableBaseModel):
    src_type: Literal["directory"] = "directory"
    src: DirectoryPath
    dest: Path
    ignores: list[str] = []

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
        for d in self.iter_dependencies:
            d.resolve(abs_dest, context)
