from collections import defaultdict
from collections.abc import AsyncGenerator
from collective.transmute import _types as t
from collective.transmute import logger
from collective.transmute.settings import is_debug
from collective.transmute.settings import pb_config
from collective.transmute.utils import exportimport as ei_utils
from collective.transmute.utils import files as file_utils
from collective.transmute.utils import item as item_utils
from collective.transmute.utils import load_all_steps
from pathlib import Path


def _add_to_drop(path: str) -> None:
    parents = item_utils.all_parents_for(path)
    valid_path = parents & pb_config.paths.filter.allowed
    if not valid_path:
        return
    already_in_drop = parents & pb_config.paths.filter.drop
    if not already_in_drop:
        pb_config.paths.filter.drop.add(path)


async def _pipeline(
    steps: tuple[t.PipelineStep],
    item: dict,
    metadata: t.MetadataInfo,
    config: t.Settings,
) -> AsyncGenerator[tuple[t.PloneItem | None, str]]:
    for step in steps:
        if not item:
            continue
        item_id = item["@id"]
        is_folderish = item.get("is_folderish", False)
        step_name = step.__name__
        add_to_drop = step_name not in pb_config.pipeline.do_not_add_drop
        result = step(item, metadata, config)
        async for item in result:
            if not item and is_folderish and add_to_drop:
                # Add this path to drop, to drop all
                # children objects as well
                _add_to_drop(item_id)
            elif item and item.pop("_is_new_item", False):
                logger.debug(
                    f"  - New item {item.get('@id')} from {step_name} for {item_id}"
                )
                async for sub_item, last_step in _pipeline(
                    steps, item, metadata, config
                ):
                    yield sub_item, last_step
    yield item, step_name


async def pipeline(src_files: t.SourceFiles, dst: Path):
    content_folder = dst / "content"
    metadata: t.MetadataInfo = await ei_utils.initialize_metadata(
        src_files, content_folder
    )
    report_step = pb_config.config.report
    steps: tuple[t.PipelineStep] = load_all_steps(pb_config.pipeline.steps)
    content_files: list[Path] = src_files.content
    total: int = len(content_files)
    processed: int = 0
    exported: defaultdict[str, int] = defaultdict(int)
    dropped: defaultdict[str, int] = defaultdict(int)
    paths = []
    async for _, raw_item in file_utils.json_reader(content_files):
        async for item, last_step in _pipeline(
            steps, raw_item, metadata, config=pb_config
        ):
            if item:
                item_files = await file_utils.export_item(item, content_folder)
                # Update metadata
                data_file = item_files.data
                paths.append((item["@id"], data_file))
                metadata._data_files_.append(data_file)
                metadata._blob_files_.extend(item_files.blob_files)
                item_uid = item["UID"]
                exported[item["@type"]] += 1
                metadata.__seen__.add(item_uid)
            else:
                # Dropped file
                dropped[last_step] += 1
                pass
            processed += 1
            if processed % report_step == 0:
                logger.info(f"  - Processed {processed}/{total} files")
    if is_debug:
        logger.debug("Converted")
        logger.debug(f"  - Total: {len(metadata.__seen__)}")
        for name, total in sorted(exported.items(), key=lambda x: x[1], reverse=True):
            logger.debug(f"  - {name}: {total}")
        logger.debug("Dropped by step")
        for name, total in sorted(dropped.items(), key=lambda x: x[1], reverse=True):
            logger.debug(f"  - {name}: {total}")
    paths = sorted(paths)
    # Sort data files according to path
    metadata._data_files_ = [i[1] for i in paths]
    metadata_file = await file_utils.export_metadata(metadata)
    return metadata_file
