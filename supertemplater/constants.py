from pathlib import Path

# ENV
SUPERTEMPLATER_HOME = "SUPERTEMPLATER_HOME"
SUPERTEMPLATER_CONFIG = "SUPERTEMPLATER_CONFIG"

# CONFIG
HOME_DEST = Path.home().joinpath(".supertemplater")
CONFIG_DEST = HOME_DEST.joinpath("config.yaml")
LOGS_DEST = HOME_DEST.joinpath("logs")
LOGS_FORMAT = "%(asctime)s | %(name)s | %(levelname)s : %(message)s"

# MISC
GIT_PROTOCOLS_PREFIXES = ["http://", "https://", "git@", "ssh://"]
