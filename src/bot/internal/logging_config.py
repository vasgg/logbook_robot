import logging.config
import sys
from datetime import datetime
from logging import Formatter
from logging.handlers import RotatingFileHandler
from pathlib import Path


class CustomFormatter(Formatter):
    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created).astimezone()
        if datefmt:
            base_time = ct.strftime("%d.%m.%Y %H:%M:%S")
            msecs = f"{int(record.msecs):03d}"
            tz = ct.strftime("%z")
            return f"{base_time}.{msecs}{tz}"
        return super().formatTime(record, datefmt)


MAIN_FORMAT = "%(asctime)s | %(message)s"
ERROR_FORMAT = "%(asctime)s [%(levelname)8s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s"
DATE_FORMAT = "%d.%m.%Y %H:%M:%S%z"


def get_logging_config(app_name: str):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "main": {
                "()": CustomFormatter,
                "format": MAIN_FORMAT,
                "datefmt": DATE_FORMAT,
            },
            "errors": {
                "()": CustomFormatter,
                "format": ERROR_FORMAT,
                "datefmt": DATE_FORMAT,
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "main",
                "stream": sys.stdout,
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "errors",
                "stream": sys.stderr,
            },
            "file": {
                "()": RotatingFileHandler,
                "level": "INFO",
                "formatter": "main",
                "filename": f"logs/{app_name}.log",
                "maxBytes": 50_000_000,  # 50MB
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": ["stdout", "stderr", "file"],
            },
        },
    }


def setup_logging(app_name: str) -> None:
    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(get_logging_config(app_name))
