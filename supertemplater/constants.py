from pathlib import Path

# ENV
SUPERTEMPLATER_HOME = "SUPERTEMPLATER_HOME"
SUPERTEMPLATER_CONFIG = "SUPERTEMPLATER_CONFIG"

# CONFIG
HOME = Path.home().joinpath(".supertemplater")
CONFIG = HOME.joinpath("config.yaml")

# MISC
GIT_PROTOCOLS_PREFIXES = ["http://", "https://", "git@", "ssh://"]
