"""
Report generation command for collective.transmute.

This module provides the CLI command for generating detailed reports about
source data, including statistics on content types, creators, review states,
and layout information.
"""

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
    """Initialize a ReportState object.
    
    Creates a new report state object with progress tracking and statistics
    containers for monitoring the report generation process.
    
    Args:
        app_layout: Application layout for UI components
        files: Iterator of files to process
        
    Returns:
        Initialized ReportState object
    """
    total = len(list(files))
    app_layout.initialize_progress(total)
    return t.ReportState(
        files=files,
        types=defaultdict(int),
        creators=defaultdict(int),
        states=defaultdict(int),
        layout=defaultdict(dict),
        type_report=defaultdict(list),
        progress=app_layout.progress,
    )


async def _create_report(dst: Path, state: t.ReportState, report_types: list) -> Path:
    """Create detailed reports from source data.
    
    Processes all source files to generate comprehensive reports including
    statistics and detailed information for specified content types.
    
    Args:
        dst: Destination directory for reports
        state: Report state containing statistics and progress tracking
        report_types: List of content types to generate detailed reports for
        
    Returns:
        Path to the main report file
    """
    async for _, item in file_utils.json_reader(state.files):
        type_ = item.get("@type")
        state.types[type_] += 1
        if type_ in report_types:
            id_ = item.get("@id")
            UID = item.get("UID")
            title = item.get("title")
            state.type_report[type_].append({
                "@id": id_,
                "UID": UID,
                "@type": type_,
                "title": title,
            })
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
    report_path = Path(dst / "report.json").resolve()
    path = await file_utils.json_dump(data, report_path)
    logger.info(f" - Wrote report to {path}")
    if report_types:
        headers = ["@id", "UID", "@type", "title"]
        for type_ in report_types:
            report_path = Path(dst / f"report_{type_}.csv").resolve()
            type_data = state.type_report.get(type_, [])
            csv_path = await file_utils.csv_dump(type_data, headers, report_path)
            logger.info(f" - Wrote types report to {csv_path}")
    return path


def parse_report_types(value: str) -> list[str]:
    """Parse comma-separated report types string.
    
    Converts a comma-separated string of content types into a list
    for detailed reporting.
    
    Args:
        value: Comma-separated string of content types
        
    Returns:
        List of content type names
    """
    types = []
    if raw_types := value.split(","):
        types = [v.strip() for v in raw_types]
    return types


@app.command()
def report(
    src: Annotated[Path, typer.Argument(help="Source path of the migration data")],
    dst: Annotated[
        Path | None, typer.Argument(help="Destination path of the report")
    ] = None,
    report_types_: Annotated[
        str,
        typer.Option(
            "--report-types",
            help="Portal types to report on. Please provide as comma-separeted values.",
        ),
    ] = "",
):
    """Generate a comprehensive report of export data.
    
    Analyzes source data and generates detailed reports including statistics
    on content types, creators, review states, and layout information.
    Optionally generates detailed CSV reports for specific content types.
    
    Args:
        src: Source directory containing export data
        dst: Destination directory for reports (defaults to current directory)
        report_types_: Comma-separated list of content types for detailed reporting
    """
    if not file_utils.check_path(src):
        raise RuntimeError(f"{src} does not exist")
    if not dst or not file_utils.check_path(dst):
        # Base path will be the current working directory
        dst = Path().cwd()
    report_types: list[str] = parse_report_types(report_types_)
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
            asyncio.run(_create_report(dst, state, report_types))
