from collective.transmute import _types as t
from collective.transmute.utils import querystring as qs_utils


def processor(item: t.PloneItem) -> t.PloneItem:
    """Fix a collection."""
    item["query"] = qs_utils.cleanup_querystring(item.get("query"))
    return item
