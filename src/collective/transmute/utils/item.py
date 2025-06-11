"""
Item utility functions for collective.transmute.

This module provides utility functions for processing Plone items and
extracting information from their paths and IDs.
"""

def all_parents_for(id_: str) -> set[str]:
    """Get all possible parent paths for a given ID.
    
    Extracts all parent path combinations from a given item ID by
    progressively removing path components from the end.
    
    Args:
        id_: Item ID/path to extract parents from
        
    Returns:
        Set of all possible parent paths
        
    Example:
        >>> all_parents_for("/Plone/folder1/folder2/item")
        {'/Plone', '/Plone/folder1', '/Plone/folder1/folder2'}
    """
    parents = []
    parts = id_.split("/")
    for idx in range(len(parts)):
        parent_path = "/".join(parts[:idx])
        if not parent_path.strip():
            continue
        parents.append(parent_path)
    return set(parents)
