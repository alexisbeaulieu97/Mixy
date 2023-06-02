from copy import deepcopy
from pathlib import Path
from typing import Literal

import tomllib

from mixy.context import Context
from mixy.utils import join_local_path

from .file_dependency import FileDependency
from .mixy_file import MixyFile


class MixyDependency(FileDependency):
    src_type: Literal["mixy"] = "mixy"

    def resolve(self, into_dir: Path, context: Context) -> None:
        abs_dest = join_local_path(into_dir, self.dest)
        abs_dest.parent.mkdir(exist_ok=True, parents=True)

        try:
            content = self.src.read_text()
            mixy_file = MixyFile(**tomllib.loads(content))

            _context = deepcopy(context)
            _context.update(**mixy_file.variables)

            resolved = _context.render(mixy_file.content)
            abs_dest.write_text(resolved)
        except UnicodeDecodeError:
            content = self.src.read_bytes()
            abs_dest.write_bytes(content)
