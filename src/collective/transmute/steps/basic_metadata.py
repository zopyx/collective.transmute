"""
Basic metadata processing step for collective.transmute.

This module handles basic metadata cleanup and processing for Plone items.
It performs simple operations like stripping whitespace from text fields.
"""

from collective.transmute import _types as t


async def process_title_description(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process title and description fields.
    
    Cleans up title and description fields by removing leading and trailing
    whitespace to ensure consistent formatting.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Item with cleaned title and description fields
    """
    for field in ("title", "description"):
        cur_value = item.get(field)
        if cur_value is not None:
            item[field] = cur_value.strip()
    yield item
