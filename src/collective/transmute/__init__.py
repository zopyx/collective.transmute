from .about import __version__  # noQA: F401
from pathlib import Path

import logging


PACKAGE_NAME = "collective.transmute"


def _setup_logging():
    from collective.transmute.settings import is_debug
    from collective.transmute.settings import pb_config

    logger = logging.getLogger(PACKAGE_NAME)
    path = Path.cwd() / pb_config.config.log_file
    logger.addHandler(logging.FileHandler(path, "a"))
    level = logging.DEBUG if is_debug else logging.INFO
    logger.setLevel(level)
    return logger


logger = _setup_logging()
