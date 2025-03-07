from collections import defaultdict
from collections.abc import Iterator
from collective.transmute import _types as t
from collective.transmute import layout
from collective.transmute import logger
from collective.transmute.utils import files as file_utils
from collective.transmute.utils import report_time
from pathlib import Path
from typing import Annotated

import asyncio
import typer


app = typer.Typer()


def _create_state(
    app_layout: layout.ApplicationLayout, files: Iterator
) -> t.ReportState:
    """Initialize a ReportState object."""
    total = len(list(files))
    app_layout.initialize_progress(total)
    return t.ReportState(
        files=files,
        types=defaultdict(int),
        creators=defaultdict(int),
        states=defaultdict(int),
        layout=defaultdict(dict),
        progress=app_layout.progress,
    )


async def _create_report(state: t.ReportState) -> Path:
    async for _, item in file_utils.json_reader(state.files):
        type_ = item.get("@type")
        state.types[type_] += 1
        review_state = item.get("review_state", "-") or "-"
        state.states[review_state] += 1
        for creator in item.get("creators", []):
            state.creators[creator] += 1
        if layout := item.get("layout"):
            type_info = state.layout[type_]
            if layout not in type_info:
                type_info[layout] = 0
            state.layout[type_][layout] += 1
        state.progress.advance()
    data = state.to_dict()
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
    app_layout = layout.ReportLayout(title=f"Report {src}")
    consoles = app_layout.consoles
    with layout.live(app_layout, redirect_stderr=False):
        # Get the src_files
        consoles.print("Getting list of files")
        src_files = file_utils.get_src_files(src)
        consoles.print(f"- Found {len(src_files.metadata)} metadata to be processed")
        consoles.print(f"- Found {len(src_files.content)} files to be processed")
        state = _create_state(app_layout, src_files.content)
        app_layout.update_layout(state)
        with report_time("Report", consoles):
            asyncio.run(_create_report(state))
