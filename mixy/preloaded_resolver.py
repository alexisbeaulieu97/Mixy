from dataclasses import dataclass
from typing import Any

from mixy.protocols.var_protocol import VarProtocol


@dataclass
class PreloadedResolver:
    variables: dict[str, Any]

    def resolve(self, var_name: str, var_config: VarProtocol) -> Any:
        return (
            self.variables[var_name]
            if var_name in self.variables
            else var_config.default
        )
