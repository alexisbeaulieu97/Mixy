from pathlib import Path

from supertemplater.constants import HOME
from supertemplater.models.base import BaseModel
from supertemplater.models.log_level import LogLevel
from supertemplater.utils import get_current_time


class LoggingSettings(BaseModel):
    location: Path = HOME.joinpath("logs")
    console_level: LogLevel = LogLevel.WARNING
    file_level: LogLevel = LogLevel.DEBUG
    file_name: str = f"{get_current_time().strftime('%Y-%m-%d_%H:%M:%S')}.log"
    logging_format: str = "%(asctime)s | %(name)s | %(levelname)s : %(message)s"

    @property
    def file_location(self) -> Path:
        return Path(self.location, self.file_name)
