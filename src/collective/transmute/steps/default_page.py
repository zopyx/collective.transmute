from collective.transmute import _types as t
from collective.transmute.settings import pb_config
from collective.transmute.utils.default_page import handle_default_page
from functools import cache


@cache
def get_keys_from_parent() -> set[str]:
    """Return keys_from_parent."""
    return set(pb_config.default_page.get("keys_from_parent", []))


async def process_default_page(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    item_uid = item["UID"]
    if parent_item := metadata.__processing_default_page__.pop(item_uid, None):
        parent_uid = parent_item["UID"]
        keys_from_parent = get_keys_from_parent()
        item = handle_default_page(parent_item, item, keys_from_parent)
        metadata.__fix_relations__[item_uid] = parent_uid
    elif default_page_uid := metadata.default_page.pop(item_uid, None):
        metadata.__processing_default_page__[default_page_uid] = item
        yield None
    else:
        yield item
