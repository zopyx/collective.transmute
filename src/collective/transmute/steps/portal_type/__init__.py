from collective.transmute import _types as t
from collective.transmute.utils import load_processor


def _pre_process(item: t.PloneItem) -> t.PloneItem:
    """Pre-process an item."""
    processor = load_processor(item["@type"])
    return processor(item)


async def process_type(
    item: t.PloneItem, metadata: t.MetadataInfo, config: t.Settings
) -> t.PloneItemGenerator:
    id_ = item["@id"]
    item = _pre_process(item)
    type_ = item["@type"]
    # Get the new type mapping
    new_type = config.types.get(type_, {}).get("portal_type")
    # Check if we have a specific mapping via type
    new_type = config.paths.get("portal_type", {}).get(id_, new_type)
    if not new_type:
        # Dropping content
        yield None
    else:
        item["@type"] = new_type
        item["_orig_type"] = type_
        yield item
