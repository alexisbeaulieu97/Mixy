import logging

from .base import NameBasedEnum


class LogLevel(NameBasedEnum):
    DISABLED = None
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
