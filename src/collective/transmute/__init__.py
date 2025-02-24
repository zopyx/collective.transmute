from .about import __version__  # noQA: F401

import logging


PACKAGE_NAME = "collective.transmute"


def _setup_logging():
    from collective.transmute.settings import is_debug

    logger = logging.getLogger(PACKAGE_NAME)
    logger.addHandler(logging.StreamHandler())
    level = logging.DEBUG if is_debug else logging.INFO
    logger.setLevel(level)
    return logger


logger = _setup_logging()
