from importlib import import_module
from collective.transmute import _types as t


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
