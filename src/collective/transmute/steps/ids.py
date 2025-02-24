from collective.transmute import _types as t


async def process_ids(
    item: dict, metadata: t.MetadataInfo, config: t.Settings
) -> t.PloneItemGenerator:
    id_ = item["@id"]
    for src, rpl in config.paths.get("cleanup", {}).items():
        id_ = id_.replace(src, rpl)
    item["@id"] = id_
    yield item
