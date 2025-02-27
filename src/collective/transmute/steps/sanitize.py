from collective.transmute import _types as t
from collective.transmute.settings import pb_config


async def process_cleanup(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    drop_keys = pb_config.sanitize.drop_keys
    item = {k: v for k, v in item.items() if k not in drop_keys}
    yield item
