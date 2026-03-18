import mixy


def test_version_is_string() -> None:
    assert isinstance(mixy.__version__, str)
    assert mixy.__version__
