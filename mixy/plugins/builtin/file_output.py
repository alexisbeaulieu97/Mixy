from pathlib import Path

from mixy.plugins.builtin import hook_impl


@hook_impl
def output(destination: Path, content: str | bytes) -> None:
    if isinstance(content, bytes):
        destination.write_bytes(content)
    else:
        destination.write_text(content)
