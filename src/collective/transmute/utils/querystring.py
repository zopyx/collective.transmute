from .portal_types import fix_portal_type


def cleanup_querystring(query: list[dict]) -> list[dict]:
    query = query if query else []
    new_query = []
    for item in query:
        index = item["i"]
        oper = item["o"]
        value = item["v"]
        match index:
            case "portal_type":
                value = [fix_portal_type(v) for v in value]
                value = [v for v in value if v.strip()]
            case "section":
                value = None
        match oper:
            # Volto is not happy with `selection.is`
            case "plone.app.querystring.operation.selection.is":
                oper = "plone.app.querystring.operation.selection.any"
        if value:
            item["v"] = value
            item["o"] = oper
            new_query.append(item)
    return new_query
