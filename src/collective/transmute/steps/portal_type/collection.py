from collective.transmute import _types as t
from collective.transmute.utils import querystring as qs_utils


async def processor(item: t.PloneItem) -> t.PloneItemGenerator:
    """Fix a collection."""
    item["query"] = qs_utils.cleanup_querystring(item.get("query"))
    yield item
