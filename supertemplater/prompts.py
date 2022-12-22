from typing import Any, TypeVar

import click
import typer

_T = TypeVar("_T")


class PromptResolver:
    def regular(self, var_name: str, default: Any) -> str:
        return typer.prompt(
            typer.style(f"(regular)", fg=typer.colors.BRIGHT_MAGENTA, bold=True)
            + " "
            + typer.style(var_name),
            default,
        )

    def multi(self, var_name: str, default: list[Any]) -> list[Any]:
        resp = typer.prompt(
            typer.style(f"(list)", fg=typer.colors.BRIGHT_BLUE, bold=True)
            + " "
            + var_name,
            default=default,
        )
        if str(default) == resp:
            return default
        return str(resp).replace(" ", "").split(",")

    def secret(self, var_name: str) -> str:
        return typer.prompt(
            typer.style("(secret)", fg=typer.colors.BRIGHT_YELLOW, bold=True)
            + " "
            + var_name,
            hide_input=True,
        )

    def confirm(self, var_name: str, default: bool) -> bool:
        return typer.confirm(
            typer.style("(confirmation)", fg=typer.colors.BRIGHT_GREEN, bold=True)
            + " "
            + var_name,
            default,
        )

    def choice(self, var_name: str, *choices: _T) -> _T:
        choice_map = {f"{i}": value for i, value in enumerate(choices, 1)}
        prompt = "\n".join(
            (
                typer.style("(select)", fg=typer.colors.BRIGHT_CYAN, bold=True),
                "\n".join("({}) {}".format(*c) for c in choice_map.items()),
                f"{var_name}",
            )
        )
        user_choice = click.prompt(
            prompt, type=click.Choice(choice_map.keys()), default="1", show_choices=False  # type: ignore
        )

        return choice_map[user_choice]
