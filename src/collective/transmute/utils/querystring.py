from .portal_types import fix_portal_type


def cleanup_querystring(query: list[dict]) -> list[dict]:
    new_query = []
    for item in query:
        index = item["i"]
        value = item["v"]
        match index:
            case "portal_type":
                value = [fix_portal_type(v) for v in value]
                value = [v for v in value if v.strip()]
            case "section":
                value = None
        if value:
            item["v"] = value
            new_query.append(item)
    return new_query
