from collective.transmute import _types as t
from collective.transmute.utils import load_processor


async def _pre_process(item: t.PloneItem) -> t.PloneItemGenerator:
    """Pre-process an item."""
    processor = load_processor(item["@type"])
    async for processed in processor(item):
        yield processed


async def process_type(
    item: t.PloneItem, metadata: t.MetadataInfo, config: t.Settings
) -> t.PloneItemGenerator:
    async for processed in _pre_process(item):
        id_ = processed["@id"]
        type_ = processed["@type"]
        # Get the new type mapping
        new_type = config.types.get(type_, {}).get("portal_type")
        # Check if we have a specific mapping via type
        new_type = config.paths.get("portal_type", {}).get(id_, new_type)
        if not new_type:
            # Dropping content
            yield None
        else:
            processed["@type"] = new_type
            processed["_orig_type"] = type_
            yield processed
