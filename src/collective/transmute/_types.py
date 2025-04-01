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

import os


type Settings = LazySettings


@dataclass
class SourceFiles:
    metadata: list[Path]
    content: list[Path]


@dataclass
class ItemFiles:
    data: str
    blob_files: list[str]


class ConsolePanel(Console):
    def __init__(self, *args, **kwargs):
        console_file = open(os.devnull, "w")  # noQA: SIM115
        super().__init__(*args, markup=True, record=True, file=console_file, **kwargs)

    def __rich_console__(self, console, options):
        texts = self.export_text(clear=False).split("\n")
        yield from texts[-options.height :]


@dataclass
class ConsoleArea:
    main: ConsolePanel
    side: ConsolePanel

    def print(self, message: str, panel_id: str = "main") -> None:
        """Print to one of the consoles."""
        console: ConsolePanel = getattr(self, panel_id)
        console.print(message)

    def print_log(self, message: str, panel_id: str = "main") -> None:
        """Print to one of the consoles."""
        self.print(message, panel_id)
        logger.info(message)


@dataclass
class PipelineProgress:
    processed: Progress
    processed_id: str
    dropped: Progress
    dropped_id: str

    def advance(self, task: str) -> None:
        progress = getattr(self, task)
        task_id = getattr(self, f"{task}_id")
        progress.advance(task_id)

    def total(self, task: str, total: int) -> None:
        progress = getattr(self, task)
        task_id = getattr(self, f"{task}_id")
        progress.update(task_id, total=total)


@dataclass
class ReportProgress:
    processed: Progress
    processed_id: str

    def advance(self, task: str = "processed") -> None:
        progress = getattr(self, task)
        task_id = getattr(self, f"{task}_id")
        progress.advance(task_id)


@dataclass
class PipelineState:
    total: int
    processed: int
    exported: defaultdict[str, int]
    dropped: defaultdict[str, int]
    progress: PipelineProgress
    seen: set = field(default_factory=set)
    uids: dict = field(default_factory=dict)


@dataclass
class ReportState:
    files: Iterator
    types: defaultdict[str, int]
    creators: defaultdict[str, int]
    states: defaultdict[str, int]
    layout: dict[str, defaultdict[str, int]]
    type_report: defaultdict[str, list]
    progress: PipelineProgress

    def to_dict(self) -> dict[str, int | dict]:
        """Return report as dictionary."""
        data = {}
        for key in ("types", "creators", "states", "layout"):
            value = getattr(self, key)
            data[key] = value
        return data


@dataclass
class MetadataInfo:
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
