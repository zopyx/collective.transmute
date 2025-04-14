from collective.transmute import _types as t
from collective.transmute.settings import pb_config

import re


PATTERNS = [
    re.compile(r"^[ _-]*(?P<path>[^ _-]*)[ _-]*$"),
]


def fix_short_id(id_: str) -> str:
    for pattern in PATTERNS:
        if match := re.match(pattern, id_):
            id_ = match.groupdict()["path"]
    id_ = id_.replace(" ", "_")
    return id_


async def process_export_prefix(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    path = item["@id"]
    for src in pb_config.paths.get("export_prefixes", []):
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
    for src, rpl in pb_config.paths.get("cleanup", {}).items():
        path = path.replace(src, rpl)
    parts = path.split("/")
    parts[-1] = fix_short_id(parts[-1])
    path = "/".join(parts)
    item["@id"] = path
    # Last element would be the id of the object
    item["id"] = parts[-1]
    yield item
