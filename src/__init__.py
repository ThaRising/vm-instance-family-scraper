import logging
import logging.config
import os
import sys
from pathlib import Path

import pypandoc
from colorama import Fore


class ColorFormatter(logging.Formatter):
    _format = "%(levelname)s %(asctime)s * %(filename)s:%(lineno)d.%(funcName)s -- %(message)s"

    FORMATS = {
        logging.DEBUG: Fore.LIGHTBLACK_EX + _format + Fore.RESET,
        logging.INFO: Fore.LIGHTBLUE_EX + _format + Fore.RESET,
        logging.WARNING: Fore.LIGHTRED_EX + _format + Fore.RESET,
        logging.ERROR: Fore.RED + _format + Fore.RESET,
        logging.CRITICAL: Fore.RED + _format + Fore.RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "color",
        },
    },
    "loggers": {
        "": {"handlers": ["console"], "level": LOG_LEVEL},
    },
    "formatters": {
        "color": {
            "()": ColorFormatter,
        },
    },
}
logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger(__name__)
logger.debug("ensure_pandoc_installed")
pypandoc.ensure_pandoc_installed()
for path in Path(__file__).parent.parent.iterdir():
    if path.suffix == ".deb" and path.stem.startswith("pandoc"):
        logger.debug("Found pandoc .deb file in project dir, cleaning up file")
        path.unlink(missing_ok=False)
