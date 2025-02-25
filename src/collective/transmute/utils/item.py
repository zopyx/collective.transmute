def all_parents_for(id_: str) -> set[str]:
    """Given an @id, return all possible parent paths."""
    parents = []
    parts = id_.split("/")
    for idx in range(len(parts)):
        parent_path = "/".join(parts[:idx])
        if not parent_path.strip():
            continue
        parents.append(parent_path)
    return set(parents)
