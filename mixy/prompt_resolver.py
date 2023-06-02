from typing import Any

import typer

from mixy.protocols.var_protocol import VarProtocol


class PromptResolver:
    def resolve(self, var_name: str, var_config: VarProtocol) -> Any:
        return typer.prompt(
            typer.style(
                var_config.description or var_name,
                fg=typer.colors.BRIGHT_GREEN,
                bold=True,
            ),
            var_config.default,
        )
