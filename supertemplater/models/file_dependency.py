from pathlib import Path
from typing import Literal

from pydantic.types import FilePath

from supertemplater.context import Context
from supertemplater.utils import join_local_path

from .base import RenderableBaseModel


class FileDependency(RenderableBaseModel):
    src_type: Literal["file"] = "file"
    src: FilePath
    dest: Path

    def resolve(self, into_dir: Path, context: Context) -> None:
        abs_dest = join_local_path(into_dir, self.dest)
        abs_dest.parent.mkdir(exist_ok=True, parents=True)
        content = self.src.read_text()
        resolved = context.render(content)
        abs_dest.write_text(resolved)
