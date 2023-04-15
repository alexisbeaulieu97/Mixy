from typing import Any

import pytest
from pytest_mock import MockerFixture

from mixy.prompt_resolver import PromptResolver

DEFAULT_VALUE_REGULAR = "default"
DEFAULT_VALUE_MULTI = ["default"]
DEFAULT_VALUE_CHOICE = "1"
CHOICES = ["a", "b", "c"]


@pytest.fixture
def resolver() -> PromptResolver:
    return PromptResolver()


@pytest.mark.parametrize("prompt_value", ["a", "b", ""])
def test_regular(mocker: MockerFixture, resolver: PromptResolver, prompt_value: str):
    return_value = prompt_value or DEFAULT_VALUE_REGULAR
    mocker.patch("typer.prompt", return_value=return_value)
    assert resolver.regular("test", DEFAULT_VALUE_REGULAR) == return_value


@pytest.mark.parametrize(
    "prompt_value, expected",
    [
        ("", DEFAULT_VALUE_MULTI),
        ("[one,two,three]", ["one", "two", "three"]),
        ("[four,five,six]", ["four", "five", "six"]),
        ("[one, two, three]", ["one", "two", "three"]),
    ],
)
def test_multi(
    mocker: MockerFixture,
    resolver: PromptResolver,
    prompt_value: str,
    expected: list[Any],
):
    return_value = prompt_value or str(DEFAULT_VALUE_MULTI)
    mocker.patch("typer.prompt", return_value=return_value)
    assert resolver.multi("test", DEFAULT_VALUE_MULTI) == expected


@pytest.mark.parametrize(
    "prompt_value, expected",
    [
        ("!@#$", "!@#$"),
        ("some_secret", "some_secret"),
    ],
)
def test_secret(
    mocker: MockerFixture, resolver: PromptResolver, prompt_value: str, expected: str
):
    return_value = prompt_value
    mocker.patch("typer.prompt", return_value=return_value)
    assert resolver.secret("test") == expected


@pytest.mark.parametrize(
    "prompt_value, expected",
    [
        ("", CHOICES[0]),
        ("1", CHOICES[0]),
        ("2", CHOICES[1]),
        ("3", CHOICES[2]),
    ],
)
def test_choice(
    mocker: MockerFixture, resolver: PromptResolver, prompt_value: str, expected: Any
):
    return_value = prompt_value or DEFAULT_VALUE_CHOICE
    mocker.patch("click.prompt", return_value=return_value)
    assert resolver.choice("test", *CHOICES) == expected
