from collective.transmute import _types as t


async def process_type(
    item: dict, metadata: t.MetadataInfo, config: t.Settings
) -> t.PloneItemGenerator:
    id_ = item["@id"]
    type_ = item["@type"]
    # Get the new type mapping
    new_type = config.types.get(type_, {}).get("portal_type")
    # Check if we have a specific mapping via type
    new_type = config.paths.get("portal_type", {}).get(id_, new_type)
    if not new_type:
        # Dropping content
        yield None
    item["@type"] = new_type
    item["_orig_type"] = type_
    yield item
