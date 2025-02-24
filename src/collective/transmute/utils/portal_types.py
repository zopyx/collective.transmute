from collective.transmute.settings import pb_config
from functools import cache


@cache
def fix_portal_type(type_: str) -> str:
    return pb_config.types.get(type_, {}).get("portal_type", "")
