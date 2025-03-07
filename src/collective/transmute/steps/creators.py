from collective.transmute import _types as t
from collective.transmute.settings import pb_config


async def process_creators(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process list of creators for an item.

    Configuration should be added to transmute.toml

    ```toml
    [principals]
    default='Plone'
    remove=['admin']
    ```
    """
    remove = pb_config.principals.remove
    current = item.get("creators", [])
    creators = [creator for creator in current if creator not in remove]
    if not creators:
        creators = [pb_config.principals.default]
    item["creators"] = creators
    yield item
