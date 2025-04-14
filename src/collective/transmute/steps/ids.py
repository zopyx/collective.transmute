from collective.transmute import _types as t
from collective.transmute.settings import pb_config
from functools import cache

import re


@cache
def get_export_prefixes() -> list[str]:
    """Return cleanup paths."""
    return pb_config.paths.get("export_prefixes", [])


@cache
def get_paths_cleanup() -> tuple[tuple[str, str], ...]:
    """Return cleanup paths."""
    return pb_config.paths.get("cleanup", {}).items()


PATTERNS = [
    re.compile(r"^[ _-]*(?P<path>[^ _-]*)[ _-]*$"),
]


def fix_short_id(id_: str) -> str:
    for pattern in PATTERNS:
        if match := re.match(pattern, id_):
            id_ = match.groupdict()["path"]
    if " " in id_:
        id_ = id_.replace(" ", "_")
    return id_


async def process_export_prefix(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    path = item["@id"]
    for src in get_export_prefixes():
        if path.startswith(src):
            path = path.replace(src, "")
    item["@id"] = path
    # Used in reports
    item["_@id"] = path
    yield item


async def process_ids(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    path = item["@id"]
    cleanup_paths = get_paths_cleanup()
    for src, rpl in cleanup_paths:
        if src in path:
            path = path.replace(src, rpl)

    parts = path.rsplit("/", maxsplit=-1)
    if parts:
        parts[-1] = fix_short_id(parts[-1])
        path = "/".join(parts)
        item["@id"] = path
        item["id"] = parts[-1]
    yield item
