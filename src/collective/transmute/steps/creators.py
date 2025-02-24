from collective.transmute import _types as t


async def process_creators(
    item: dict, metadata: t.MetadataInfo, config: t.Settings
) -> t.PloneItemGenerator:
    remove = config.principals.remove
    current = item.get("creators", [])
    creators = [creator for creator in current if creator not in remove]
    if not creators:
        creators = [config.principals.default]
    item["creators"] = creators
    yield item
