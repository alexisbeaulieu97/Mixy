from typing import Any

import pytest

from supertemplater.preloaded_resolver import PreloadedResolver

RESOLVER_VARIABLES = {
    "a": 1,
    "b": 2,
    "c": 3,
    "d": ["test"],
    "e": ["test_1", "test_2"],
    "secret_a": "shhh",
    "secret_b": "very secret",
    "confirm_a": True,
    "confirm_b": False,
    "choice_a": "a",
    "choice_b": "b",
    "choice_c": "c"
}

DEFAULT_VALUE_REGULAR = "default"
DEFAULT_VALUE_MULTI = ["default"]
DEFAULT_VALUE_CONFIRM = True
CHOICES = ["a", "b", "c"]


@pytest.fixture
def resolver() -> PreloadedResolver:
    return PreloadedResolver(RESOLVER_VARIABLES)


@pytest.mark.parametrize(
    "prompt_value, expected",
    [
        ("", DEFAULT_VALUE_REGULAR),
        ("a", RESOLVER_VARIABLES["a"]),
        ("b", RESOLVER_VARIABLES["b"]),
        ("c", RESOLVER_VARIABLES["c"]),
    ],
)
def test_regular(resolver: PreloadedResolver, prompt_value: str, expected: str):
    result = resolver.regular(prompt_value, DEFAULT_VALUE_REGULAR)
    assert result == expected


@pytest.mark.parametrize(
    "prompt_value, expected",
    [
        ("", DEFAULT_VALUE_MULTI),
        ("d", RESOLVER_VARIABLES["d"]),
        ("e", RESOLVER_VARIABLES["e"]),
    ],
)
def test_multi(resolver: PreloadedResolver, prompt_value: str, expected: list[Any]):
    result = resolver.multi(prompt_value, DEFAULT_VALUE_MULTI)
    assert result == expected


@pytest.mark.parametrize(
    "prompt_value, expected",
    [
        ("secret_a", RESOLVER_VARIABLES["secret_a"]),
        ("secret_b", RESOLVER_VARIABLES["secret_b"]),
    ],
)
def test_secret(resolver: PreloadedResolver, prompt_value: str, expected: str):
    result = resolver.secret(prompt_value)
    assert result == expected


@pytest.mark.parametrize(
    "prompt_value, expected",
    [
        ("", DEFAULT_VALUE_CONFIRM),
        ("confirm_a", RESOLVER_VARIABLES["confirm_a"]),
        ("confirm_b", RESOLVER_VARIABLES["confirm_b"]),
    ],
)
def test_confirm(resolver: PreloadedResolver, prompt_value: str, expected: bool):
    result = resolver.confirm(prompt_value, DEFAULT_VALUE_CONFIRM)
    assert result == expected


@pytest.mark.parametrize(
    "prompt_value, expected",
    [
        ("choice_a", RESOLVER_VARIABLES["choice_a"]),
        ("choice_b", RESOLVER_VARIABLES["choice_b"]),
        ("choice_c", RESOLVER_VARIABLES["choice_c"]),
        ("invalid", None),
    ],
)
def test_choice(resolver: PreloadedResolver, prompt_value: str, expected: Any):
    if expected is None:
        with pytest.raises(Exception):
            resolver.choice(prompt_value, *CHOICES)
    else:
        result = resolver.choice(prompt_value, *CHOICES)
        assert result == expected
