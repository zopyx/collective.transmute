from collective.transmute import _types as t
from collective.transmute.utils.portal_types import fix_portal_type


async def process_constraints(
    item: dict, metadata: t.MetadataInfo, config: t.Settings
) -> t.PloneItemGenerator:
    key = "exportimport.constrains"
    if old_constrains := item.pop(key, None):
        constrains = {}
        for c_type, value in old_constrains.items():
            value = {fix_portal_type(v) for v in value}
            # Remove empty value
            value.pop("", None)
            constrains[c_type] = list(value)
        item[key] = constrains
    yield item
