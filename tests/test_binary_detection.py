from pathlib import Path

from mixy.infrastructure.rendering.binary_detection import is_binary

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "templates"


def test_binary_detection_uses_extension_blocklist() -> None:
    assert is_binary(FIXTURES_DIR / "logo.png") is True


def test_binary_detection_uses_null_byte_heuristic(tmp_path: Path) -> None:
    candidate = tmp_path / "opaque.data"
    candidate.write_bytes(b"abc\x00def")

    assert is_binary(candidate) is True


def test_binary_detection_leaves_text_files_renderable() -> None:
    assert is_binary(FIXTURES_DIR / "hello.txt") is False
