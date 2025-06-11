"""
Type definitions for the collective.transmute package.

This module contains all the core type definitions, dataclasses, and utility classes
used throughout the package for data transformation, pipeline processing, and UI
management.
"""

from collections import defaultdict
from collections.abc import AsyncGenerator
from collections.abc import Callable
from collections.abc import Iterator
from collective.transmute import logger
from dataclasses import dataclass
from dataclasses import field
from dynaconf.base import LazySettings
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from typing import TypedDict

import logging
import os


# Type alias for settings
Settings = LazySettings


@dataclass
class SourceFiles:
    """Container for source file paths used in data transformation.
    
    Attributes:
        metadata: List of paths to metadata files
        content: List of paths to content files
    """
    metadata: list[Path]
    content: list[Path]


@dataclass
class ItemFiles:
    """Container for processed item files.
    
    Attributes:
        data: Path to the data file for the item
        blob_files: List of blob file paths associated with the item
    """
    data: str
    blob_files: list[str]


class ConsolePanel(Console):
    """Custom console panel that redirects output to null device.
    
    This console panel is used for UI components where output should be
    captured but not displayed directly to avoid interference with the
    rich UI layout.
    """
    def __init__(self, *args, **kwargs):
        console_file = open(os.devnull, "w")  # noQA: SIM115
        super().__init__(*args, markup=True, record=True, file=console_file, **kwargs)

    def __rich_console__(self, console, options):
        """Export console text for display in rich UI components."""
        texts = self.export_text(clear=False).split("\n")
        yield from texts[-options.height :]


@dataclass
class ConsoleArea:
    """Container for multiple console panels used in UI layout.
    
    Attributes:
        main: Main console panel for primary output
        side: Side console panel for secondary output
        ui: Flag to enable/disable UI mode
    """
    main: ConsolePanel
    side: ConsolePanel
    ui: bool = True

    def disable_ui(self):
        """Disable UI mode and redirect output to standard logging."""
        self.ui = False
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        logger.addHandler(console)

    def print(self, message: str, panel_id: str = "main") -> None:
        """Print a message to the specified console panel.
        
        Args:
            message: The message to print
            panel_id: Which panel to print to ('main' or 'side')
        """
        if self.ui:
            console: ConsolePanel = getattr(self, panel_id)
            console.print(message)
        else:
            logger.info(message)

    def print_log(self, message: str, panel_id: str = "main") -> None:
        """Print a message to console and also log it.
        
        Args:
            message: The message to print and log
            panel_id: Which panel to print to ('main' or 'side')
        """
        if self.ui:
            self.print(message, panel_id)
        logger.info(message)

    def debug(self, message: str, panel_id: str = "main") -> None:
        """Write a debug message to the logger.
        
        Args:
            message: The debug message
            panel_id: Unused parameter for consistency with other methods
        """
        logger.debug(message)


@dataclass
class PipelineProgress:
    """Progress tracking for pipeline processing operations.
    
    Attributes:
        processed: Progress bar for processed items
        processed_id: ID of the processed progress task
        dropped: Progress bar for dropped items
        dropped_id: ID of the dropped progress task
    """
    processed: Progress
    processed_id: str
    dropped: Progress
    dropped_id: str

    def advance(self, task: str) -> None:
        """Advance the specified progress task by one.
        
        Args:
            task: Which task to advance ('processed' or 'dropped')
        """
        progress = getattr(self, task)
        task_id = getattr(self, f"{task}_id")
        progress.advance(task_id)

    def total(self, task: str, total: int) -> None:
        """Update the total count for the specified progress task.
        
        Args:
            task: Which task to update ('processed' or 'dropped')
            total: New total count
        """
        progress = getattr(self, task)
        task_id = getattr(self, f"{task}_id")
        progress.update(task_id, total=total)


@dataclass
class ReportProgress:
    """Progress tracking for reporting operations.
    
    Attributes:
        processed: Progress bar for processed items
        processed_id: ID of the processed progress task
    """
    processed: Progress
    processed_id: str

    def advance(self, task: str = "processed") -> None:
        """Advance the specified progress task by one.
        
        Args:
            task: Which task to advance (defaults to 'processed')
        """
        progress = getattr(self, task)
        task_id = getattr(self, f"{task}_id")
        progress.advance(task_id)


@dataclass
class PipelineItemReport(TypedDict):
    """Report data structure for individual pipeline items.
    
    Contains information about the transformation of a single item from
    source to destination format.
    
    Attributes:
        filename: Name of the source file
        src_path: Source path of the item
        src_uid: Source UID of the item
        src_type: Source type of the item
        dst_path: Destination path of the item
        dst_uid: Destination UID of the item
        dst_type: Destination type of the item
        last_step: Name of the last processing step
    """
    filename: str
    src_path: str
    src_uid: str
    src_type: str
    dst_path: str
    dst_uid: str
    dst_type: str
    last_step: str


@dataclass
class PipelineState:
    """State container for pipeline processing operations.
    
    Tracks the overall state of a data transformation pipeline including
    progress, statistics, and metadata.
    
    Attributes:
        total: Total number of items to process
        processed: Number of items processed so far
        exported: Dictionary counting exported items by type
        dropped: Dictionary counting dropped items by step
        progress: Progress tracking object
        seen: Set of UIDs that have been processed
        uids: Dictionary mapping old UIDs to new UIDs
        path_transforms: List of transformation reports for each item
    """
    total: int
    processed: int
    exported: defaultdict[str, int]
    dropped: defaultdict[str, int]
    progress: PipelineProgress
    seen: set = field(default_factory=set)
    uids: dict = field(default_factory=dict)
    path_transforms: list[PipelineItemReport] = field(default_factory=list)


@dataclass
class ReportState:
    """State container for reporting operations.
    
    Tracks the state of report generation including file processing
    and statistics collection.
    
    Attributes:
        files: Iterator over files to process
        types: Dictionary counting items by type
        creators: Dictionary counting items by creator
        states: Dictionary counting items by review state
        layout: Dictionary of layout statistics
        type_report: Dictionary of type-specific reports
        progress: Progress tracking object
    """
    files: Iterator
    types: defaultdict[str, int]
    creators: defaultdict[str, int]
    states: defaultdict[str, int]
    layout: dict[str, defaultdict[str, int]]
    type_report: defaultdict[str, list]
    progress: PipelineProgress

    def to_dict(self) -> dict[str, int | dict]:
        """Convert report state to dictionary format.
        
        Returns:
            Dictionary containing the report statistics
        """
        data = {}
        for key in ("types", "creators", "states", "layout"):
            value = getattr(self, key)
            data[key] = value
        return data


@dataclass
class MetadataInfo:
    """Container for metadata information during data transformation.
    
    Stores various metadata fields and processing information used
    throughout the transformation pipeline.
    
    Attributes:
        path: Path to the metadata file
        __version__: Version of the metadata format
        __processing_default_page__: Default page processing settings
        __fix_relations__: Relation fixing settings
        _blob_files_: List of blob file paths
        _data_files_: List of data file paths
        default_page: Default page configuration
        local_permissions: Local permission settings
        local_roles: Local role assignments
        ordering: Content ordering information
        relations: Content relation mappings
    """
    path: Path
    __version__: str = "1.0.0"
    __processing_default_page__: dict = field(default_factory=dict)
    __fix_relations__: dict = field(default_factory=dict)
    _blob_files_: list = field(default_factory=list)
    _data_files_: list = field(default_factory=list)
    default_page: dict = field(default_factory=dict)
    local_permissions: dict = field(default_factory=dict)
    local_roles: dict = field(default_factory=dict)
    ordering: dict = field(default_factory=dict)
    relations: dict = field(default_factory=dict)


PloneItem = TypedDict("PloneItem", {"@id": str, "@type": str, "UID": str, "id": str})

PloneItemGenerator = AsyncGenerator[PloneItem | None]

PipelineStep = Callable[[], PloneItemGenerator]
ItemProcessor = Callable[[], PloneItem]
