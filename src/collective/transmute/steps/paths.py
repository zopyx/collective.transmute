from collective.transmute import _types as t
from collective.transmute.settings import pb_config


def _is_valid_path(path_filter: dict, path: str) -> bool:
    """Check if path is allowed to be processed."""
    status = True
    if drop := path_filter.get("drop", []):
        for prefix in drop:
            if path.startswith(prefix):
                return False
    if allowed := path_filter.get("allowed", []):
        status = False
        for prefix in allowed:
            if path.startswith(prefix):
                return True
    return status


async def process_paths(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    id_ = item["@id"]
    path_filter = pb_config.paths.get("filter", {})
    if not _is_valid_path(path_filter, id_):
        yield None
    else:
        yield item
