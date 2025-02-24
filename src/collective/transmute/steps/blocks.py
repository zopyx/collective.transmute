from collective.html2blocks.converter import volto_blocks
from collective.transmute import _types as t
from collective.transmute.utils import querystring as qs_utils


def _process_collection(item: dict, blocks: list[dict]) -> list[dict]:
    """Add a listing block."""
    # TODO: Process query to remove old types
    query = qs_utils.cleanup_querystring(item.get("query"))
    if query:
        block = {
            "@type": "listing",
            "headlineTag": "h2",
            "querystring": {
                "query": query,
                "sort_on": item["sort_on"],
                "sort_order": (
                    "ascending" if item["sort_reversed"] == "" else "descending"
                ),
            },
        }
        blocks.append(block)
    return blocks


def _get_default_blocks(type_: str, config: t.Settings) -> list[dict] | None:
    default_blocks = config.types[type_].get("blocks", None)
    return [b.to_dict() for b in default_blocks] if default_blocks else None


async def process_blocks(
    item: dict, metadata: t.MetadataInfo, config: t.Settings
) -> t.PloneItemGenerator:
    type_ = item["@type"]
    blocks = _get_default_blocks(type_, config)
    if blocks:
        if item["_orig_type"] == "Collection":
            blocks = _process_collection(item, blocks)
        text = item.get("text", {})
        src = text.get("data", "") if text else ""
        blocks_info = volto_blocks(source=src, default_blocks=blocks)
        item.update(blocks_info)
    yield item
