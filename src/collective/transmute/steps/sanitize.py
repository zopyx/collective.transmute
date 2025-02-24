from collective.transmute import _types as t


async def process_cleanup(
    item: dict, metadata: t.MetadataInfo, config: t.Settings
) -> t.PloneItemGenerator:
    drop_keys = config.sanitize.drop_keys
    item = {k: v for k, v in item.items() if k not in drop_keys}
    yield item
