from pathlib import Path

from supertemplater.models.base import BaseModel
from supertemplater.models.log_level import LogLevel
from supertemplater.utils import get_current_time, get_home


class LoggingSettings(BaseModel):
    console_level: LogLevel = LogLevel.WARNING
    file_level: LogLevel = LogLevel.DEBUG
    file_dest_dir: Path = get_home().joinpath("logs")
    file_name: str = f"{get_current_time().strftime('%Y-%m-%d_%H:%M:%S')}.log"
    logging_format: str = "%(asctime)s | %(name)s | %(levelname)s : %(message)s"

    @property
    def file_dest(self) -> Path:
        return Path(self.file_dest_dir, self.file_name)
