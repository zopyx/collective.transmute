from collections.abc import AsyncGenerator
from collective.transmute import _types as t
from collective.transmute.utils import files
from dataclasses import asdict
from pathlib import Path


async def initialize_metadata(src_files: t.SourceFiles, dst: Path) -> t.MetadataInfo:
    path = dst / "__metadata__.json"
    metadata_files = src_files.metadata
    data = {}
    async for filename, content in files.json_reader(metadata_files):
        key = filename.replace("export_", "").replace(".json", "")
        data[key] = content

    # Process default_pages
    default_page = {
        item["uuid"]: item["default_page_uuid"] for item in data.get("defaultpages", [])
    }
    local_permissions: dict[str, dict] = {}
    # Process local_roles
    local_roles: dict[str, dict] = {
        item["uuid"]: {"local_roles": item["localroles"]}
        for item in data.get("localroles", [])
    }
    ordering: dict[str, dict] = {
        item["uuid"]: item["order"] for item in data.get("ordering", [])
    }
    relations: list[dict] = data.get("relations", [])

    return t.MetadataInfo(
        path=path,
        default_page=default_page,
        local_permissions=local_permissions,
        local_roles=local_roles,
        ordering=ordering,
        relations=relations,
    )


async def prepare_metadata_file(
    metadata: t.MetadataInfo, state: t.PipelineState, debug: bool = False
) -> AsyncGenerator[tuple[dict, Path]]:
    data: dict = asdict(metadata)
    path: Path = data.pop("path")
    if debug:
        data["__seen__"] = list(state.seen)
        debug_path = path.parent / "__debug_metadata__.json"
        yield data, debug_path
    remove = [key for key in data if key.startswith("__") and key != "__version__"]

    for key in ["default_page", "ordering", "local_roles"]:
        data[key] = {k: v for k, v in data[key].items() if k in state.seen}
    data["relations"] = []
    for item in remove:
        data.pop(item)
    yield data, path
