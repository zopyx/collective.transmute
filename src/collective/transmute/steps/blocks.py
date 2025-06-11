"""
Block processing step for collective.transmute.

This module handles the transformation of content blocks from legacy Plone
format to modern Volto blocks format. It processes different types of content
including collections, topics, and folders, converting them to appropriate
block structures.
"""

from collective.html2blocks.converter import volto_blocks
from collective.transmute import _types as t
from collective.transmute.settings import pb_config


def _blocks_collection(item: dict, blocks: list[dict]) -> list[dict]:
    """Add a listing block for collection/topic content.
    
    Processes collection and topic items by converting their query parameters
    and display settings into a listing block configuration.
    
    Args:
        item: The collection/topic item to process
        blocks: List of existing blocks to append to
        
    Returns:
        Updated list of blocks with the new listing block
    """
    # TODO: Process query to remove old types
    query = item.get("query")
    if query:
        querystring = {
            "query": query,
        }

        if "sort_on" in item:
            querystring["sort_on"] = item["sort_on"]

        if "sort_order" in item:
            querystring["sort_order"] = (
                ("ascending" if item["sort_reversed"] == "" else "descending"),
            )
            querystring["sort_order_boolean"] = True

        block = {
            "@type": "listing",
            "headline": "",
            "headlineTag": "h2",
            "querystring": querystring,
            "b_size": item.get("item_count", 10),
            "limit": item.get("limit", 1000),
            "styles": {},
            "variation": "summary",
        }
        blocks.append(block)
    return blocks


def _blocks_folder(item: dict, blocks: list[dict]) -> list[dict]:
    """Add a listing block for folder content.
    
    Processes folder items by converting their layout settings into
    appropriate listing block variations.
    
    Args:
        item: The folder item to process
        blocks: List of existing blocks to append to
        
    Returns:
        Updated list of blocks with the new listing block
    """
    possible_variations = {
        "listing_view": "listing",
        "summary_view": "summary",
        "tabular_view": "listing",
        "full_view": "summary",
        "album_view": "imageGallery",
        "galeria_de_fotos": "imageGallery",
        "galeria_de_albuns": "imageGallery",
    }
    if variation := item.get("layout"):
        variation = possible_variations.get(variation)

    if not variation:
        variation = "listing"
    block = {
        "@type": "listing",
        "headline": "",
        "headlineTag": "h2",
        "styles": {},
        "variation": variation,
    }
    blocks.append(block)
    return blocks


BLOCKS_ORIG_TYPE = {
    "Collection": _blocks_collection,
    "Topic": _blocks_collection,
    "Folder": _blocks_folder,
}


def _get_default_blocks(
    type_: str, has_image: bool, has_description: bool
) -> list[dict]:
    """Get default blocks for a content type.
    
    Retrieves and filters default blocks based on content type and
    available content (image, description).
    
    Args:
        type_: Content type name
        has_image: Whether the item has an image
        has_description: Whether the item has a description
        
    Returns:
        List of default blocks for the content type
    """
    type_info = pb_config.types.get(type_, {})
    default_blocks = type_info.get("override_blocks", type_info.get("blocks", None))
    blocks = [b.to_dict() for b in default_blocks] if default_blocks else []
    if default_blocks:
        blocks = []
        for block in [b.to_dict() for b in default_blocks]:
            block_type = block["@type"]
            if (block_type == "leadimage" and not has_image) or (
                block_type == "description" and not has_description
            ):
                continue
            blocks.append(block)
    return blocks


async def process_blocks(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process content blocks for a Plone item.
    
    Main pipeline step that converts legacy Plone content into modern
    Volto blocks format. Handles different content types and applies
    appropriate transformations.
    
    Args:
        item: The Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        The processed item with updated block structure
    """
    type_ = item["@type"]
    has_image = bool(item.get("image"))
    has_description = has_description = bool(
        item.get("description") is not None and item.get("description", "").strip()
    )
    blocks = _get_default_blocks(type_, has_image, has_description)
    # Blocks defined somewhere else
    item_blocks = item.pop("_blocks_", [])
    if blocks or item_blocks:
        blocks.extend(item_blocks)
        orig_type = item.get("_orig_type")
        if processor := BLOCKS_ORIG_TYPE.get(orig_type):
            blocks = processor(item, blocks)
        text = item.get("text", {})
        src = text.get("data", "") if text else ""
        blocks_info = volto_blocks(source=src, default_blocks=blocks)
        item.update(blocks_info)
    yield item
