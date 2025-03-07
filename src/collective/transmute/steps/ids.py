from collective.transmute import _types as t
from collective.transmute.settings import pb_config


async def process_ids(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    id_ = item["@id"]
    for src, rpl in pb_config.paths.get("cleanup", {}).items():
        id_ = id_.replace(src, rpl)
    item["@id"] = id_
    # Last element would be the id of the object
    item["id"] = id_.split("/")[-1]
    yield item
