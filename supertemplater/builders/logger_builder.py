import logging
import os
import sys
from pathlib import Path
from typing import TextIO

from supertemplater.models.log_level import LogLevel


class LoggerBuilder:
    def __init__(self, name: str, level: LogLevel) -> None:
        self.name = name
        self.level = level
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level.value)

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
