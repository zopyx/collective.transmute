"""
Utility functions for the collective.transmute package.

This module provides various utility functions for step loading, processor
management, data sorting, and timing operations used throughout the
transformation pipeline.
"""

from collective.transmute import _types as t
from collective.transmute import logger
from collective.transmute.settings import pb_config
from contextlib import contextmanager
from datetime import datetime
from functools import cache
from importlib import import_module


@cache
def load_step(name: str) -> t.PipelineStep:
    """Load a step from a dotted name.
    
    Dynamically imports and loads a pipeline step function based on its
    dotted module path. Uses caching to avoid repeated imports.
    
    Args:
        name: Dotted name of the step function (e.g., 'module.function')
        
    Returns:
        The loaded pipeline step function
        
    Raises:
        RuntimeError: If the step function cannot be found or loaded
    """
    mod_name, func_name = name.rsplit(".", 1)
    try:
        mod = import_module(mod_name)
    except ModuleNotFoundError:
        raise RuntimeError(f"Function {name} not available") from None
    func = getattr(mod, func_name, None)
    if not func:
        raise RuntimeError(f"Function {name} not available") from None
    return func


def load_all_steps(names: list[str]) -> tuple[t.PipelineStep]:
    """Load multiple pipeline steps from a list of dotted names.
    
    Loads all specified pipeline steps and returns them as a tuple for
    use in the transformation pipeline.
    
    Args:
        names: List of dotted names for step functions
        
    Returns:
        Tuple of loaded pipeline step functions
    """
    steps = []
    for name in names:
        steps.append(load_step(name))
    return tuple(steps)


def check_steps(names: list[str]) -> list[tuple[str, bool]]:
    """Check the availability of pipeline steps.
    
    Verifies whether each specified step can be loaded without actually
    loading them. Useful for validation and error reporting.
    
    Args:
        names: List of dotted names for step functions
        
    Returns:
        List of tuples containing (step_name, is_available)
    """
    steps: list[tuple[str, bool]] = []
    for name in names:
        status = True
        try:
            load_step(name)
        except RuntimeError:
            status = False
        steps.append((name, status))
    return steps


@cache
def load_processor(type_: str) -> t.ItemProcessor:
    """Load a processor for a given type.
    
    Loads a type-specific processor function based on the configuration.
    Falls back to a default processor if no type-specific one is configured.
    
    Args:
        type_: Content type for which to load a processor
        
    Returns:
        The loaded processor function
        
    Raises:
        RuntimeError: If the processor function cannot be found or loaded
    """
    types_config = pb_config.types
    name = types_config.get(type_, {}).get("processor")
    if not name:
        name = types_config.processor
    mod_name, func_name = name.rsplit(".", 1)
    try:
        mod = import_module(mod_name)
    except ModuleNotFoundError:
        raise RuntimeError(f"Function {name} not available") from None
    func = getattr(mod, func_name, None)
    if not func:
        raise RuntimeError(f"Function {name} not available") from None
    return func


def sort_data(
    data: dict[str, int], reverse: bool = True
) -> tuple[tuple[str, int], ...]:
    """Sort data by values in descending or ascending order.
    
    Sorts a dictionary by its values and returns the result as a tuple
    of (key, value) pairs.
    
    Args:
        data: Dictionary to sort
        reverse: Whether to sort in descending order (default: True)
        
    Returns:
        Sorted tuple of (key, value) pairs
    """
    return tuple(sorted(data.items(), key=lambda x: x[1], reverse=reverse))


@contextmanager
def report_time(title: str, consoles: t.ConsoleArea):
    """Context manager for timing operations and reporting duration.
    
    Measures the time taken for operations and reports the duration
    through the console area. Useful for performance monitoring.
    
    Args:
        title: Title for the timing report
        consoles: Console area for output display
    """
    start = datetime.now()
    msg = f"{title} started at {start}"
    consoles.print_log(msg)
    yield
    finish = datetime.now()
    msg = f"{title} ended at {finish}\n{title} took {(finish - start).seconds} seconds"
    consoles.print_log(msg)
    logger.info(msg)
