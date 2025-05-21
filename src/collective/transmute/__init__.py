from .about import __version__  # noQA: F401
from pathlib import Path

import logging


PACKAGE_NAME = "collective.transmute"


def _setup_logging():
    from collective.transmute.settings import is_debug
    from collective.transmute.settings import pb_config

    level = logging.DEBUG if is_debug else logging.INFO

    logger = logging.getLogger(PACKAGE_NAME)
    logger.setLevel(level)

    path = Path.cwd() / pb_config.config.log_file
    file_handler = logging.FileHandler(path, "a")
    file_handler.setLevel(level)
    file_formatter = logging.Formatter("%(levelname)s: %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


logger = _setup_logging()
