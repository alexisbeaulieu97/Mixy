import logging
import os
import sys
from pathlib import Path
from typing import TextIO

from supertemplater.models.log_level import LogLevel
from supertemplater.settings import LoggingSettings


class LoggerBuilder:
    def __init__(self, name: str, level: LogLevel = LogLevel.DEBUG) -> None:
        self.name = name
        self.level = level
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level.value)

    @staticmethod
    def with_settings(
        settings: LoggingSettings, name: str, level: LogLevel = LogLevel.DEBUG
    ) -> logging.Logger:
        builder = LoggerBuilder(name, level)
        if settings.file_level != LogLevel.DISABLED:
            builder.with_file_logging(
                settings.file_path, settings.file_level, settings.logging_format
            )
        if settings.console_level != LogLevel.DISABLED:
            builder.with_console_logging(
                settings.console_level, settings.logging_format
            )
        return builder.build()

    def _configure_handler(
        self, handler: logging.Handler, level: LogLevel, log_format: str
    ) -> None:
        handler.setLevel(level.value)
        handler.setFormatter(logging.Formatter(log_format))

    def with_console_logging(
        self, level: LogLevel, log_format: str, stream: TextIO = ...
    ) -> "LoggerBuilder":
        stream = sys.stderr if stream is ... else stream
        handler = logging.StreamHandler(stream)
        self._configure_handler(handler, level, log_format)
        self.logger.addHandler(handler)
        return self

    def with_file_logging(
        self, dest: Path, level: LogLevel, log_format: str
    ) -> "LoggerBuilder":
        os.makedirs(dest.parent, exist_ok=True)
        handler = logging.FileHandler(dest)
        self._configure_handler(handler, level, log_format)
        self.logger.addHandler(handler)
        return self

    def build(self) -> logging.Logger:
        return self.logger
