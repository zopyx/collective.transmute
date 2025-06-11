"""
Transmute command module for data transformation operations.

This module provides the main CLI command for transforming data from
collective.exportimport format to plone.exportimport format. It handles
the orchestration of the transformation pipeline and provides various
options for controlling the transformation process.
"""

from collections import defaultdict
from collective.transmute import _types as t
from collective.transmute import layout
from collective.transmute.pipeline import pipeline
from collective.transmute.utils import files as file_utils
from collective.transmute.utils import report_time
from pathlib import Path
from typing import Annotated

import asyncio
import typer


app = typer.Typer()


def _create_state(app_layout: layout.ApplicationLayout, total: int) -> t.PipelineState:
    """Initialize a PipelineState object.
    
    Creates a new pipeline state object with progress tracking and statistics
    containers for monitoring the transformation process.
    
    Args:
        app_layout: Application layout for UI components
        total: Total number of items to process
        
    Returns:
        Initialized PipelineState object
    """
    app_layout.initialize_progress(total)
    return t.PipelineState(
        total,
        processed=0,
        exported=defaultdict(int),
        dropped=defaultdict(int),
        progress=app_layout.progress,
    )


def _remove_existing_data(dst: Path, consoles: t.ConsoleArea):
    """Remove existing data in the destination directory.
    
    Cleans up any existing content in the destination directory before
    starting the transformation process.
    
    Args:
        dst: Destination directory path
        consoles: Console area for output display
    """
    consoles.print_log(f"Removing existing content in {dst}")
    file_utils.remove_data(dst, consoles)


def _run_pipeline(
    src: Path,
    dst: Path,
    app_layout: layout.TransmuteLayout,
    consoles: t.ConsoleArea,
    clean_up: bool,
    write_report: bool,
):
    """Execute the main transformation pipeline.
    
    Orchestrates the complete transformation process including file discovery,
    state initialization, pipeline execution, and cleanup.
    
    Args:
        src: Source directory path
        dst: Destination directory path
        app_layout: Application layout for UI
        consoles: Console area for output display
        clean_up: Whether to clean up existing destination data
        write_report: Whether to write a detailed CSV report
    """
    consoles.print(f"Listing content in {src}")
    src_files = file_utils.get_src_files(src)
    total = len(src_files.content)
    consoles.print(f"- Found {total} files to be processed")
    if clean_up:
        _remove_existing_data(dst, consoles)
    state = _create_state(app_layout, total)
    app_layout.update_layout(state)
    with report_time("Transmute", consoles):
        asyncio.run(pipeline(src_files, dst, state, write_report, consoles))


@app.command()
def run(
    src: Annotated[Path, typer.Argument(help="Source path of the migration")],
    dst: Annotated[Path, typer.Argument(help="Destination path of the migration")],
    write_report: Annotated[
        bool,
        typer.Option(
            help="Should we write a csv report with all path transformations?"
        ),
    ] = False,
    clean_up: Annotated[
        bool,
        typer.Option(help="Should we remove all existing files in the dst?"),
    ] = False,
    ui: Annotated[
        bool,
        typer.Option(help="Use rich UI"),
    ] = True,
):
    """Transmutes data from src folder (in collective.exportimport format)
    to plone.exportimport format in the dst folder.
    
    This is the main command for transforming Plone content from the legacy
    collective.exportimport format to the modern plone.exportimport format.
    The transformation process includes content type conversion, metadata
    updates, and file reorganization.
    
    Args:
        src: Source directory containing collective.exportimport data
        dst: Destination directory for plone.exportimport output
        write_report: Generate a detailed CSV report of transformations
        clean_up: Remove existing content in destination before processing
        ui: Enable rich terminal UI for progress monitoring
    """
    # Check if paths exist
    file_utils.check_paths(src, dst)
    app_layout = layout.TransmuteLayout(title=f"{src} -> {dst}")
    consoles = app_layout.consoles
    if ui:
        with layout.live(app_layout, redirect_stderr=False):
            _run_pipeline(src, dst, app_layout, consoles, clean_up, write_report)
    else:
        consoles.disable_ui()
        _run_pipeline(src, dst, app_layout, consoles, clean_up, write_report)
