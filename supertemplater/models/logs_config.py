import logging
from pathlib import Path

from supertemplater.builders.logger_builder import LoggerBuilder
from supertemplater.constants import LOGS_DEST, LOGS_FORMAT
from supertemplater.utils import get_current_time

from .base import RenderableBaseModel
from .log_level import LogLevel


class LogsConfig(RenderableBaseModel):
    console_log_level: LogLevel = LogLevel.WARNING
    file_log_level: LogLevel = LogLevel.DEBUG
    file_dest: Path = LOGS_DEST.joinpath(
        f"{get_current_time().strftime('%Y-%m-%d_%H:%M:%S')}.log"
    )
    logs_format: str = LOGS_FORMAT

    def get_logger(self, name: str) -> logging.Logger:
        builder = LoggerBuilder(name, LogLevel.DEBUG)

        if self.console_log_level != LogLevel.DISABLED:
            builder.with_console_logging(self.console_log_level, self.logs_format)
        if self.file_log_level != LogLevel.DISABLED:
            builder.with_file_logging(
                self.file_dest, self.file_log_level, self.logs_format
            )
        return builder.build()
