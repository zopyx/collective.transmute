from collective.transmute import logger
from collective.transmute.pipeline import pipeline
from collective.transmute.utils import files as file_utils
from datetime import datetime
from pathlib import Path
from typing import Annotated

import asyncio
import typer


app = typer.Typer()


@app.command()
def run(
    src: Annotated[Path, typer.Argument(help="Source path of the migration")],
    dst: Annotated[Path, typer.Argument(help="Destination path of the migration")],
):
    """Transmutes data from src folder (in collective.exportimport format)
    to plone.exportimport format in the dst folder.
    """
    if not file_utils.check_path(src):
        raise RuntimeError(f"{src} does not exist")
    if not file_utils.check_path(dst):
        raise RuntimeError(f"{dst} does not exist")
    # Get the src_files
    logger.info("Getting list of files")
    src_files = file_utils.get_src_files(src)
    logger.info(f"- Found {len(src_files.metadata)} metadata to be processed")
    logger.info(f"- Found {len(src_files.content)} files to be processed")
    start = datetime.now()
    logger.debug(f"Transmute started at {start}")
    asyncio.run(pipeline(src_files, dst))
    finish = datetime.now()
    logger.debug(f"Transmute ended at {finish}")
    logger.debug(f"Transmute took {(finish - start).seconds} seconds")
