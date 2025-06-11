"""
Custom content type processors for collective.transmute.

This module provides processors for transforming custom content types
to standard Plone content types during migration.
"""

from collective.transmute import _types as t
from collective.transmute.settings import pb_config
from datetime import datetime
from typing import Dict, Any, List


def _map_field_value(item: Dict[str, Any], old_field: str, new_field: str):
    """Map a field value from old field name to new field name.
    
    Args:
        item: The item to modify
        old_field: Original field name
        new_field: New field name
    """
    if old_field in item:
        item[new_field] = item.pop(old_field)


def _process_text_field(text_data: Any) -> Dict[str, str]:
    """Process text field data into standard format.
    
    Args:
        text_data: Raw text data
        
    Returns:
        Standardized text field dictionary
    """
    if isinstance(text_data, dict):
        return text_data
    elif isinstance(text_data, str):
        return {"data": text_data, "content-type": "text/html"}
    else:
        return {"data": str(text_data), "content-type": "text/plain"}


async def custom_news_processor(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process custom news items.
    
    Transforms CustomNewsItem to standard News Item with proper
    field mapping and metadata.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Transformed News Item
    """
    
    # Get field mapping configuration
    field_mapping = pb_config.get("field_mapping", {})
    
    # Map custom fields to standard fields
    _map_field_value(item, "custom_title", "title")
    _map_field_value(item, "custom_body", "text")
    _map_field_value(item, "custom_image", "image")
    _map_field_value(item, "custom_date", "effective")
    _map_field_value(item, "custom_author", "creators")
    _map_field_value(item, "custom_tags", "subjects")
    
    # Process text field
    if text_data := item.get("text"):
        item["text"] = _process_text_field(text_data)
    
    # Set standard metadata
    item["@type"] = "News Item"
    item["effective"] = item.get("effective") or item.get("created")
    item["expires"] = item.get("expires")
    
    # Handle creators field
    if creators := item.get("creators"):
        if isinstance(creators, str):
            item["creators"] = [creators]
    
    # Handle subjects/tags
    if subjects := item.get("subjects"):
        if isinstance(subjects, str):
            item["subjects"] = [subjects]
    
    yield item


async def custom_event_processor(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process custom event items.
    
    Transforms CustomEvent to standard Event with proper
    field mapping and event-specific metadata.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Transformed Event
    """
    
    # Get field mapping configuration
    field_mapping = pb_config.get("field_mapping", {})
    
    # Map custom fields to standard fields
    _map_field_value(item, "custom_title", "title")
    _map_field_value(item, "custom_body", "text")
    _map_field_value(item, "custom_image", "image")
    _map_field_value(item, "event_date", "start")
    _map_field_value(item, "event_end_date", "end")
    _map_field_value(item, "event_location", "location")
    
    # Process text field
    if text_data := item.get("text"):
        item["text"] = _process_text_field(text_data)
    
    # Set standard metadata
    item["@type"] = "Event"
    
    # Handle event dates
    if start_date := item.get("start"):
        if isinstance(start_date, str):
            try:
                # Parse and format date
                parsed_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                item["start"] = parsed_date.isoformat()
            except ValueError:
                # Keep original if parsing fails
                pass
    
    if end_date := item.get("end"):
        if isinstance(end_date, str):
            try:
                parsed_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                item["end"] = parsed_date.isoformat()
            except ValueError:
                pass
    
    # Handle event location
    if location := item.get("location"):
        if isinstance(location, dict):
            # Extract address components
            item["location"] = location.get("address", str(location))
    
    yield item


async def legacy_document_processor(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process legacy document items.
    
    Transforms LegacyDocument to standard Document with
    legacy field cleanup and standardization.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Transformed Document
    """
    
    # Get field mapping configuration
    field_mapping = pb_config.get("field_mapping", {})
    
    # Map legacy fields to standard fields
    _map_field_value(item, "legacy_title", "title")
    _map_field_value(item, "legacy_body", "text")
    _map_field_value(item, "legacy_author", "creators")
    _map_field_value(item, "legacy_date", "effective")
    
    # Process text field
    if text_data := item.get("text"):
        item["text"] = _process_text_field(text_data)
    
    # Set standard metadata
    item["@type"] = "Document"
    
    # Clean up legacy metadata
    legacy_fields = [
        "legacy_id", "legacy_type", "legacy_metadata",
        "old_workflow_state", "legacy_permissions"
    ]
    
    for field in legacy_fields:
        item.pop(field, None)
    
    # Handle creators field
    if creators := item.get("creators"):
        if isinstance(creators, str):
            item["creators"] = [creators]
    
    yield item


async def custom_gallery_processor(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process custom gallery items.
    
    Transforms CustomGallery to Folder with image gallery
    block structure.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Transformed Folder with gallery structure
    """
    
    # Get field mapping configuration
    field_mapping = pb_config.get("field_mapping", {})
    
    # Map custom fields to standard fields
    _map_field_value(item, "gallery_title", "title")
    _map_field_value(item, "gallery_description", "description")
    
    # Set standard metadata
    item["@type"] = "Folder"
    
    # Handle gallery images
    if gallery_images := item.pop("gallery_images", None):
        # Create image gallery block
        if "blocks" not in item:
            item["blocks"] = {}
        
        item["blocks"]["gallery-1"] = {
            "@type": "imageGallery",
            "images": gallery_images,
            "styles": {"variation": "gallery"}
        }
    
    # Handle gallery metadata
    if gallery_metadata := item.pop("gallery_metadata", None):
        # Extract relevant metadata
        if isinstance(gallery_metadata, dict):
            item["subjects"] = gallery_metadata.get("tags", [])
            item["effective"] = gallery_metadata.get("created")
    
    yield item


async def process_custom_types(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Main processor for custom content types.
    
    Routes items to appropriate custom processors based on
    their content type.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Processed item
    """
    
    content_type = item.get("@type", "")
    
    # Route to appropriate processor
    if content_type == "CustomNewsItem":
        async for processed_item in custom_news_processor(item, metadata):
            yield processed_item
    elif content_type == "CustomEvent":
        async for processed_item in custom_event_processor(item, metadata):
            yield processed_item
    elif content_type == "LegacyDocument":
        async for processed_item in legacy_document_processor(item, metadata):
            yield processed_item
    elif content_type == "CustomGallery":
        async for processed_item in custom_gallery_processor(item, metadata):
            yield processed_item
    else:
        # Pass through unchanged for standard types
        yield item 