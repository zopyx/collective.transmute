from collective.transmute import _types as t
from collective.transmute.settings import pb_config


async def process_data_override(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Overwrite an item data (identified by its @id) with information from settings.

    Configuration should be added to transmute.toml

    ```toml
    [data_override]
    "/campus/areia/noticias" = { "title" = "Notícias" }
    "/campus/areia/home" = { "exclude_from_nav" = true, "review_state" = "private" }
    ```
    """
    id_ = item["@id"]
    override = pb_config.get("data_override", {}).get(id_, {})
    for key, value in override.items():
        item[key] = value
    yield item
