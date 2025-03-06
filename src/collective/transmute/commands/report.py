from collections import defaultdict
from collections.abc import Iterator
from collective.transmute import logger
from collective.transmute import settings
from collective.transmute.utils import files as file_utils
from datetime import datetime
from pathlib import Path
from typing import Annotated

import asyncio
import typer


app = typer.Typer()


async def _create_report(files: Iterator) -> Path:
    data: dict[str, defaultdict] = {
        "types": defaultdict(int),
        "creators": defaultdict(int),
        "states": defaultdict(int),
        "layout": defaultdict(dict),
    }
    total = len(list(files))
    processed = 0
    async for _, item in file_utils.json_reader(files):
        processed += 1
        if processed % settings.pb_config.config.report == 0:
            logger.info(f"  - Processed {processed}/{total} files")
        type_ = item.get("@type")
        data["types"][type_] += 1
        review_state = item.get("review_state", "-") or "-"
        data["states"][review_state] += 1
        for creator in item.get("creators", []):
            data["creators"][creator] += 1
        if layout := item.get("layout"):
            type_info = data["layout"][type_]
            if layout not in type_info:
                type_info[layout] = 0
            data["layout"][type_][layout] += 1
    report_path = Path("report.json").resolve()
    path = await file_utils.json_dump(data, report_path)
    logger.info(f" - Wrote report to {path}")
    return path


@app.command()
def report(
    src: Annotated[Path, typer.Argument(help="Source path of the migration")],
):
    """Generates a json file with a report of export data in src directory."""
    if not file_utils.check_path(src):
        raise RuntimeError(f"{src} does not exist")
    # Get the src_files
    logger.info("Getting list of files")
    src_files = file_utils.get_src_files(src)
    logger.info(f"- Found {len(src_files.metadata)} metadata to be processed")
    logger.info(f"- Found {len(src_files.content)} files to be processed")
    start = datetime.now()
    logger.debug(f"Report started at {start}")
    asyncio.run(_create_report(src_files.content))
    finish = datetime.now()
    logger.debug(f"Report ended at {finish}")
    logger.debug(f"Report took {(finish - start).seconds} seconds")
