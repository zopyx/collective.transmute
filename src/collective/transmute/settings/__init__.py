"""
Settings management for collective.transmute.

This module provides configuration management using Dynaconf, supporting
TOML configuration files, environment variables, and validation. It handles
the loading and validation of all package settings.
"""

from dynaconf import Dynaconf
from dynaconf import Validator
from pathlib import Path
from typing import Any


def _as_set(value: Any) -> set:
    """Cast a value to a set.
    
    Converts various input types to a set, handling empty or None values
    by returning an empty set.
    
    Args:
        value: Value to convert to set
        
    Returns:
        Set containing the value elements
    """
    value = value if value else []
    return set(value)


def _settings() -> Dynaconf:
    """Initialize and configure Dynaconf settings.
    
    Sets up the configuration system with default TOML file, environment
    variable support, and validation rules.
    
    Returns:
        Configured Dynaconf settings object
    """
    local_path = Path(__file__).parent
    default = local_path / "default.toml"
    settings = Dynaconf(
        envvar_prefix="PB_MIGRACAO",
        preload=[default],
        settings_files=["transmute.toml"],
        merge_enabled=True,
        validators=[
            Validator("paths.filter.allowed", cast=_as_set, default=set()),
            Validator("paths.filter.drop", cast=_as_set, default=set()),
        ],
    )
    if not len(settings.pipeline.get("steps")):
        settings.pipeline.steps = settings.pipeline.default_steps
    return settings


# Global configuration object
pb_config: Dynaconf = _settings()

# Debug mode flag
is_debug: bool = pb_config.config.debug

__all__ = ["is_debug", "pb_config"]
