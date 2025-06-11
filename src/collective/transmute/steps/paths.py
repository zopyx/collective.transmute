"""
Path filtering step for collective.transmute.

This module handles path-based filtering of items during the transformation
process. It allows for inclusion/exclusion of items based on their paths
using configurable filter rules.
"""

from collective.transmute import _types as t
from collective.transmute.settings import pb_config


def _is_valid_path(path_filter: dict, path: str) -> bool:
    """Check if a path is allowed to be processed.
    
    Validates a path against configured filter rules including drop and
    allowed path prefixes.
    
    Args:
        path_filter: Dictionary containing filter configuration
        path: Path to validate
        
    Returns:
        True if path should be processed, False if it should be dropped
    """
    status = True
    if drop := path_filter.get("drop", []):
        for prefix in drop:
            if path.startswith(prefix):
                return False
    if allowed := path_filter.get("allowed", []):
        status = False
        for prefix in allowed:
            if path.startswith(prefix):
                return True
    return status


async def process_paths(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process item paths for filtering.
    
    Main pipeline step that filters items based on their paths using
    configured filter rules. Items that don't match the filter criteria
    are dropped from processing.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Item if it passes path filtering, None if it should be dropped
    """
    id_ = item["@id"]
    path_filter = pb_config.paths.get("filter", {})
    if not _is_valid_path(path_filter, id_):
        yield None
    else:
        yield item
