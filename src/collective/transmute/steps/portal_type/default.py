from collective.transmute import _types as t


async def processor(item: t.PloneItem) -> t.PloneItemGenerator:
    """Process a PloneItem."""
    yield item
