from collective.transmute import _types as t
from importlib import import_module


def load_step(name: str) -> t.PipelineStep:
    """Load a step from a dotted name."""
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
    steps = []
    for name in names:
        steps.append(load_step(name))
    return tuple(steps)


def check_steps(names: list[str]) -> list[tuple[str, bool]]:
    steps: list[tuple[str, bool]] = []
    for name in names:
        status = True
        try:
            load_step(name)
        except RuntimeError:
            status = False
        steps.append((name, status))
    return steps


def load_processor(type_: str, config: t.Settings) -> t.ItemProcessor:
    """Load a processor for a given type."""
    types_config = config.types
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
