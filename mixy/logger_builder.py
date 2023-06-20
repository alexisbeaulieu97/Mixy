import logging
import os
import sys
from pathlib import Path
from typing import Self, TextIO

from mixy.models.log_level import LogLevel
from mixy.settings.logging_settings import LoggingSettings


class LoggerBuilder:
    def __init__(self, name: str, level: LogLevel = LogLevel.DEBUG) -> None:
        self.name = name
        self.level = level
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(
            self.level.value if self.level.value is not None else logging.NOTSET
        )

    @staticmethod
    def with_settings(
        settings: LoggingSettings, name: str, level: LogLevel = LogLevel.DEBUG
    ) -> logging.Logger:
        builder = LoggerBuilder(name, level)
        if settings.file_level != LogLevel.DISABLED:
            builder.with_file_logging(
                settings.file_location, settings.file_level, settings.logging_format
            )
        if settings.console_level != LogLevel.DISABLED:
            builder.with_console_logging(
                settings.console_level, settings.logging_format
            )
        return builder.build()

    def _configure_handler(
        self, handler: logging.Handler, level: LogLevel, log_format: str
    ) -> None:
        handler.setLevel(level.value if level.value is not None else logging.NOTSET)
        handler.setFormatter(logging.Formatter(log_format))

    def with_console_logging(
        self, level: LogLevel, log_format: str, stream: TextIO = ...
    ) -> Self:
        stream = sys.stderr if stream is ... else stream
        handler = logging.StreamHandler(stream)
        self._configure_handler(handler, level, log_format)
        self.logger.addHandler(handler)
        return self

    def with_file_logging(self, dest: Path, level: LogLevel, log_format: str) -> Self:
        dest = Path(dest)
        try:
            os.makedirs(dest.parent, exist_ok=True)
            handler = logging.FileHandler(dest)
        except Exception as e:
            raise Exception(
                f"Failed to setup file handler at location {dest}. Error: {str(e)}"
            ) from e
        self._configure_handler(handler, level, log_format)
        self.logger.addHandler(handler)
        return self

    def build(self) -> logging.Logger:
        return self.logger
