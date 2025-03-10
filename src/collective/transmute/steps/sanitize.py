from collective.transmute import _types as t
from collective.transmute.settings import pb_config
from functools import cache


@cache
def get_drop_keys(has_blocks: bool) -> set[str]:
    drop_keys: set[str] = set(pb_config.sanitize.drop_keys)
    if has_blocks:
        block_keys: set[str] = set(pb_config.sanitize.block_keys)
        drop_keys = drop_keys | block_keys
    return drop_keys


async def process_cleanup(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    has_blocks = "blocks" in item
    drop_keys = get_drop_keys(has_blocks)
    item = {k: v for k, v in item.items() if k not in drop_keys}
    yield item
