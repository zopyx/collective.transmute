"""
Collective Transmute - Data Transformation Utility for Plone Migration

This package provides a comprehensive data transformation pipeline for converting
data from collective.exportimport format to plone.exportimport format. It includes
a modular step-based processing system, rich UI for monitoring progress, and
various utilities for data migration tasks.

The package consists of several key components:
- Pipeline: Core processing engine for data transformation
- Steps: Modular transformation steps for different data types
- Utils: Helper functions for file operations, reporting, and data processing
- Layout: Rich UI components for progress monitoring and reporting
- Settings: Configuration management using TOML files
- Commands: CLI interface for various operations

Main functionality:
- Transform Plone content from collective.exportimport to plone.exportimport format
- Process different content types with customizable transformation steps
- Generate detailed reports of transformation results
- Provide rich terminal UI for monitoring migration progress
- Support for custom transformation rules and configurations

Usage:
    python -m collective.transmute transmute run <source_path> <destination_path>
    python -m collective.transmute report <source_path>
    python -m collective.transmute settings
    python -m collective.transmute sanity
"""

from .about import __version__  # noQA: F401
from pathlib import Path

import logging


PACKAGE_NAME = "collective.transmute"


def _setup_logging():
    """Set up logging configuration for the package.
    
    Configures logging with appropriate level (DEBUG if debug mode is enabled,
    otherwise INFO) and creates a file handler for logging to a configurable
    log file path.
    
    Returns:
        logging.Logger: Configured logger instance for the package.
    """
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
