from collective.transmute import _types as t
from collective.transmute.settings import pb_config


def _is_valid_state(state_filter: dict[str, list], review_state: str) -> bool:
    """Check if review_state is allowed to be processed."""
    allowed = state_filter.get("allowed", [])
    status = True
    if review_state and allowed:
        status = review_state in allowed
    return status


async def process_review_state(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    review_state: str = item.get("review_state", "")
    state_filter: dict[str, list] = pb_config.review_state.get("filter", {})
    if not _is_valid_state(state_filter, review_state):
        yield None
    else:
        yield item
