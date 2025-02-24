from collective.transmute import _types as t


def _merge_items(parent_item: dict, item: dict, config: dict) -> dict:
    keys_from_parent = config.get("keys_from_parent", [])
    filtered = {k: v for k, v in parent_item.items() if k in keys_from_parent}
    item.update(filtered)
    return item


async def process_default_page(
    item: t.PloneItem, metadata: t.MetadataInfo, config: t.Settings
) -> t.PloneItemGenerator:
    item_uid = item["UID"]
    if parent_item := metadata.__processing_default_page__.pop(item_uid, None):
        parent_uid = parent_item["UID"]
        item = _merge_items(parent_item, item, config.default_page)
        metadata.__fix_relations__[item_uid] = parent_uid
    elif default_page_uid := metadata.default_page.pop(item_uid, None):
        metadata.__processing_default_page__[default_page_uid] = item
        yield None
    else:
        yield item
