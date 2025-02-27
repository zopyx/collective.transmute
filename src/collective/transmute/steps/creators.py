from collective.transmute import _types as t
from collective.transmute.settings import pb_config


async def process_creators(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    remove = pb_config.principals.remove
    current = item.get("creators", [])
    creators = [creator for creator in current if creator not in remove]
    if not creators:
        creators = [pb_config.principals.default]
    item["creators"] = creators
    yield item
