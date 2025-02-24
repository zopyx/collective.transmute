from dynaconf import Dynaconf
from pathlib import Path


def _settings() -> Dynaconf:
    """Compute settings"""
    local_path = Path(__file__).parent
    default = local_path / "default.toml"
    return Dynaconf(
        envvar_prefix="PB_MIGRACAO",
        preload=[default],
        settings_files=["transmute.toml"],
        merge_enabled=True,
    )


pb_config: Dynaconf = _settings()

is_debug: bool = pb_config.config.debug

__all__ = ["is_debug,pb_config"]
