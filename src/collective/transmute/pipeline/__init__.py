from collections.abc import AsyncGenerator
from collective.transmute import _types as t
from collective.transmute.settings import is_debug
from collective.transmute.settings import pb_config
from collective.transmute.utils import exportimport as ei_utils
from collective.transmute.utils import files as file_utils
from collective.transmute.utils import item as item_utils
from collective.transmute.utils import load_all_steps
from collective.transmute.utils import sort_data
from pathlib import Path


def _add_to_drop(path: str) -> None:
    parents = item_utils.all_parents_for(path)
    valid_path = parents & pb_config.paths.filter.allowed
    if not valid_path:
        return
    already_in_drop = parents & pb_config.paths.filter.drop
    if not already_in_drop:
        pb_config.paths.filter.drop.add(path)


def _report_final_state(consoles: t.ConsoleArea, state: t.PipelineState):
    consoles.print_log("Converted")
    consoles.print_log(f"  - Total: {len(state.seen)}")
    for name, total in sort_data(state.exported):
        consoles.print_log(f"   - {name}: {total}")
    consoles.print_log("Dropped by step")
    for name, total in sort_data(state.dropped):
        consoles.print_log(f"  - {name}: {total}")


async def _pipeline(
    steps: tuple[t.PipelineStep],
    item: dict,
    metadata: t.MetadataInfo,
    consoles: t.ConsoleArea,
) -> AsyncGenerator[tuple[t.PloneItem | None, str, bool]]:
    for step in steps:
        if not item:
            continue
        item_id = item["@id"]
        item_uid = item["UID"]
        is_folderish = item.get("is_folderish", False)
        step_name = step.__name__
        add_to_drop = step_name not in pb_config.pipeline.do_not_add_drop
        result = step(item, metadata)
        async for item in result:
            if not item and is_folderish and add_to_drop:
                # Add this path to drop, to drop all
                # children objects as well
                _add_to_drop(item_id)
            elif item and item.pop("_is_new_item", False):
                msg = f" - New: {item.get('UID')} (from {step_name} for {item_uid})"
                consoles.print(msg)
                async for sub_item, last_step, _ in _pipeline(
                    steps, item, metadata, consoles
                ):
                    yield sub_item, last_step, True
    yield item, step_name, False


async def pipeline(
    src_files: t.SourceFiles,
    dst: Path,
    state: t.PipelineState,
    consoles: t.ConsoleArea,
):
    content_folder = dst / "content"
    metadata: t.MetadataInfo = await ei_utils.initialize_metadata(
        src_files, content_folder
    )
    steps: tuple[t.PipelineStep] = load_all_steps(pb_config.pipeline.steps)
    content_files: list[Path] = src_files.content
    # Pipeline state variables
    total = state.total
    processed = state.processed
    exported = state.exported
    dropped = state.dropped
    progress = state.progress
    seen = state.seen
    paths = []
    async for _, raw_item in file_utils.json_reader(content_files):
        async for item, last_step, is_new in _pipeline(
            steps, raw_item, metadata, consoles
        ):
            processed += 1
            progress.advance("processed")
            if is_new:
                total += 1
                progress.total("processed", total)
            if not item:
                # Dropped file
                progress.advance("dropped")
                dropped[last_step] += 1
                continue
            item_files = await file_utils.export_item(item, content_folder)
            # Update metadata
            data_file = item_files.data
            paths.append((item["@id"], data_file))
            metadata._blob_files_.extend(item_files.blob_files)
            item_uid = item["UID"]
            exported[item["@type"]] += 1
            seen.add(item_uid)
    if is_debug:
        _report_final_state(consoles, state)
    paths = sorted(paths)
    consoles.print_log("Writing metadata files")
    # Sort data files according to path
    metadata._data_files_ = [i[1] for i in paths]
    metadata_file = await file_utils.export_metadata(metadata, state)
    consoles.print_log(f" - Wrote {metadata_file}")
    return metadata_file
