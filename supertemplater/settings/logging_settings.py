from pathlib import Path
from typing import Optional

from supertemplater.models.base import BaseModel
from supertemplater.models.log_level import LogLevel
from supertemplater.utils import get_current_time, get_home


class LoggingSettings(BaseModel):
    console_level: LogLevel = LogLevel.WARNING
    file_level: LogLevel = LogLevel.DEBUG
    logs_dest: Optional[Path] = None
    file_name: str = f"{get_current_time().strftime('%Y-%m-%d_%H:%M:%S')}.log"
    logging_format: str = "%(asctime)s | %(name)s | %(levelname)s : %(message)s"

    @property
    def logs_home(self) -> Path:
        return (
            self.logs_dest
            if self.logs_dest is not None
            else get_home().joinpath("logs")
        )

    @property
    def file_path(self) -> Path:
        return Path(self.logs_home, self.file_name)
