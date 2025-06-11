"""
ID processing step for collective.transmute.

This module handles the transformation and cleanup of item IDs and paths
during the data transformation process. It removes export prefixes,
cleans up path components, and ensures proper ID formatting.
"""

from collective.transmute import _types as t
from collective.transmute.settings import pb_config
from functools import cache
from urllib import parse

import re


@cache
def get_export_prefixes() -> list[str]:
    """Get export prefixes to remove from paths.
    
    Returns:
        List of export prefixes configured for removal
    """
    return pb_config.paths.get("export_prefixes", [])


@cache
def get_paths_cleanup() -> tuple[tuple[str, str], ...]:
    """Get path cleanup mappings.
    
    Returns:
        Tuple of (source, replacement) pairs for path cleanup
    """
    return pb_config.paths.get("cleanup", {}).items()


PATTERNS = [
    re.compile(r"^[ _-]*(?P<path>[^ _-]*)[ _-]*$"),
]


def fix_short_id(id_: str) -> str:
    """Fix short ID by removing leading/trailing separators and spaces.
    
    Cleans up ID strings by removing unnecessary separators and converting
    spaces to underscores.
    
    Args:
        id_: ID string to clean up
        
    Returns:
        Cleaned ID string
    """
    for pattern in PATTERNS:
        if match := re.match(pattern, id_):
            id_ = match.groupdict()["path"]
    if " " in id_:
        id_ = id_.replace(" ", "_")
    return id_


async def process_export_prefix(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process export prefixes in item paths.
    
    Removes configured export prefixes from item paths to clean up
    the path structure.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Item with cleaned path
    """
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
    """Process item IDs and paths.
    
    Main pipeline step that cleans up item IDs and paths by removing
    export prefixes, applying path cleanup rules, and fixing short IDs.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Item with cleaned IDs and paths
    """
    path = parse.unquote(item["@id"].replace(" ", "_"))
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
