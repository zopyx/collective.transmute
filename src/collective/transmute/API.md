# Collective Transmute API Documentation

This document provides detailed API documentation for the `collective.transmute` package, including all modules, classes, and functions.

## Package Overview

The `collective.transmute` package is organized into several key modules:

- **Core Types**: `_types.py` - Type definitions and dataclasses
- **Pipeline**: `pipeline/` - Main processing engine
- **Steps**: `steps/` - Transformation step modules
- **Utils**: `utils/` - Utility functions
- **Layout**: `layout/` - UI components
- **Settings**: `settings/` - Configuration management
- **Commands**: `commands/` - CLI interface

## Core Types (`_types.py`)

### Data Classes

#### `SourceFiles`
Container for source file paths used in data transformation.

```python
@dataclass
class SourceFiles:
    metadata: list[Path]  # List of paths to metadata files
    content: list[Path]   # List of paths to content files
```

#### `ItemFiles`
Container for processed item files.

```python
@dataclass
class ItemFiles:
    data: str              # Path to the data file for the item
    blob_files: list[str]  # List of blob file paths associated with the item
```

#### `ConsoleArea`
Container for multiple console panels used in UI layout.

```python
@dataclass
class ConsoleArea:
    main: ConsolePanel  # Main console panel for primary output
    side: ConsolePanel  # Side console panel for secondary output
    ui: bool = True     # Flag to enable/disable UI mode
    
    def disable_ui(self) -> None
    def print(self, message: str, panel_id: str = "main") -> None
    def print_log(self, message: str, panel_id: str = "main") -> None
    def debug(self, message: str, panel_id: str = "main") -> None
```

#### `PipelineState`
State container for pipeline processing operations.

```python
@dataclass
class PipelineState:
    total: int                                    # Total number of items to process
    processed: int                                # Number of items processed so far
    exported: defaultdict[str, int]              # Dictionary counting exported items by type
    dropped: defaultdict[str, int]               # Dictionary counting dropped items by step
    progress: PipelineProgress                   # Progress tracking object
    seen: set = field(default_factory=set)       # Set of UIDs that have been processed
    uids: dict = field(default_factory=dict)     # Dictionary mapping old UIDs to new UIDs
    path_transforms: list[PipelineItemReport] = field(default_factory=list)  # Transformation reports
```

#### `MetadataInfo`
Container for metadata information during data transformation.

```python
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
```

### Type Aliases

```python
PloneItem = TypedDict("PloneItem", {"@id": str, "@type": str, "UID": str, "id": str})
PloneItemGenerator = AsyncGenerator[PloneItem | None]
PipelineStep = Callable[[], PloneItemGenerator]
ItemProcessor = Callable[[], PloneItem]
```

## Pipeline Module (`pipeline/__init__.py`)

### Main Functions

#### `pipeline()`
Main pipeline function for data transformation.

```python
async def pipeline(
    src_files: SourceFiles,
    dst: Path,
    state: PipelineState,
    write_report: bool,
    consoles: ConsoleArea,
) -> Path
```

**Parameters:**
- `src_files`: Source file paths (metadata and content)
- `dst`: Destination directory path
- `state`: Pipeline state for tracking progress and statistics
- `write_report`: Whether to write a detailed CSV report
- `consoles`: Console area for output display

**Returns:**
- Path to the generated metadata file

## Utils Module (`utils/__init__.py`)

### Core Functions

#### `load_step()`
Load a step from a dotted name.

```python
@cache
def load_step(name: str) -> PipelineStep
```

**Parameters:**
- `name`: Dotted name of the step function (e.g., 'module.function')

**Returns:**
- The loaded pipeline step function

**Raises:**
- `RuntimeError`: If the step function cannot be found or loaded

#### `load_all_steps()`
Load multiple pipeline steps from a list of dotted names.

```python
def load_all_steps(names: list[str]) -> tuple[PipelineStep]
```

**Parameters:**
- `names`: List of dotted names for step functions

**Returns:**
- Tuple of loaded pipeline step functions

#### `load_processor()`
Load a processor for a given type.

```python
@cache
def load_processor(type_: str) -> ItemProcessor
```

**Parameters:**
- `type_`: Content type for which to load a processor

**Returns:**
- The loaded processor function

#### `sort_data()`
Sort data by values in descending or ascending order.

```python
def sort_data(
    data: dict[str, int], 
    reverse: bool = True
) -> tuple[tuple[str, int], ...]
```

**Parameters:**
- `data`: Dictionary to sort
- `reverse`: Whether to sort in descending order (default: True)

**Returns:**
- Sorted tuple of (key, value) pairs

#### `report_time()`
Context manager for timing operations and reporting duration.

```python
@contextmanager
def report_time(title: str, consoles: ConsoleArea)
```

**Parameters:**
- `title`: Title for the timing report
- `consoles`: Console area for output display

## File Utils (`utils/files.py`)

### Core Functions

#### `json_dumps()`
Dump data to JSON bytes.

```python
def json_dumps(data: dict | list) -> bytes
```

**Parameters:**
- `data`: Data to convert to JSON

**Returns:**
- JSON data as bytes

#### `json_dump()`
Dump JSON data to a file.

```python
async def json_dump(data: dict | list, path: Path) -> Path
```

**Parameters:**
- `data`: Data to write as JSON
- `path`: File path to write to

**Returns:**
- Path to the written file

#### `get_src_files()`
Get source files from a directory.

```python
def get_src_files(src: Path) -> SourceFiles
```

**Parameters:**
- `src`: Source directory to scan

**Returns:**
- SourceFiles object containing categorized file paths

#### `export_item()`
Export a Plone item to the destination format.

```python
async def export_item(item: PloneItem, parent_folder: Path) -> ItemFiles
```

**Parameters:**
- `item`: Plone item to export
- `parent_folder`: Parent directory for the export

**Returns:**
- ItemFiles object containing data file path and blob file paths

## Layout Module (`layout/__init__.py`)

### Classes

#### `ApplicationLayout`
Base application layout class.

```python
class ApplicationLayout:
    title: str
    layout: Layout
    consoles: ConsoleArea
    progress: ReportProgress | PipelineProgress
    
    def __init__(self, title: str)
    def _create_layout(self, title: str) -> Layout
    def update_layout(self, state: PipelineState | ReportState)
    def initialize_progress(self, total: int)
```

#### `TransmuteLayout`
Layout for the main transmute operation.

```python
class TransmuteLayout(ApplicationLayout):
    def _create_layout(self, title: str) -> Layout
    def update_layout(self, state: PipelineState)
    def initialize_progress(self, total: int)
```

#### `ReportLayout`
Layout for report generation operations.

```python
class ReportLayout(ApplicationLayout):
    def _create_layout(self, title: str) -> Layout
    def update_layout(self, state: ReportState)
    def initialize_progress(self, total: int)
```

### Functions

#### `live()`
Create a live display for the application layout.

```python
def live(app_layout: ApplicationLayout, redirect_stderr: bool = True) -> Live
```

**Parameters:**
- `app_layout`: Application layout to display
- `redirect_stderr`: Whether to redirect stderr to the display

**Returns:**
- Rich Live display object

## Steps Modules

### Blocks Step (`steps/blocks.py`)

#### `process_blocks()`
Process content blocks for a Plone item.

```python
async def process_blocks(
    item: PloneItem, 
    metadata: MetadataInfo
) -> PloneItemGenerator
```

**Parameters:**
- `item`: The Plone item to process
- `metadata`: Metadata information for the transformation

**Yields:**
- The processed item with updated block structure

### IDs Step (`steps/ids.py`)

#### `process_ids()`
Process item IDs and paths.

```python
async def process_ids(
    item: PloneItem, 
    metadata: MetadataInfo
) -> PloneItemGenerator
```

**Parameters:**
- `item`: Plone item to process
- `metadata`: Metadata information for the transformation

**Yields:**
- Item with cleaned IDs and paths

### Paths Step (`steps/paths.py`)

#### `process_paths()`
Process item paths for filtering.

```python
async def process_paths(
    item: PloneItem, 
    metadata: MetadataInfo
) -> PloneItemGenerator
```

**Parameters:**
- `item`: Plone item to process
- `metadata`: Metadata information for the transformation

**Yields:**
- Item if it passes path filtering, None if it should be dropped

## Settings Module (`settings/__init__.py`)

### Global Variables

```python
pb_config: Dynaconf = _settings()  # Global configuration object
is_debug: bool = pb_config.config.debug  # Debug mode flag
```

### Functions

#### `_settings()`
Initialize and configure Dynaconf settings.

```python
def _settings() -> Dynaconf
```

**Returns:**
- Configured Dynaconf settings object

## Commands Modules

### Transmute Command (`commands/transmute.py`)

#### `run()`
Transmutes data from src folder to plone.exportimport format.

```python
@app.command()
def run(
    src: Path,
    dst: Path,
    write_report: bool = False,
    clean_up: bool = False,
    ui: bool = True,
)
```

**Parameters:**
- `src`: Source directory containing collective.exportimport data
- `dst`: Destination directory for plone.exportimport output
- `write_report`: Generate a detailed CSV report of transformations
- `clean_up`: Remove existing content in destination before processing
- `ui`: Enable rich terminal UI for progress monitoring

### Report Command (`commands/report.py`)

#### `report()`
Generate a comprehensive report of export data.

```python
@app.command()
def report(
    src: Path,
    dst: Path | None = None,
    report_types_: str = "",
)
```

**Parameters:**
- `src`: Source directory containing export data
- `dst`: Destination directory for reports (defaults to current directory)
- `report_types_`: Comma-separated list of content types for detailed reporting

## CLI Interface (`cli.py`)

### Main Application

```python
app = typer.Typer(no_args_is_help=True)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Welcome to transmute, the utility to transform data from
    collective.exportimport to plone.exportimport.
    """
    pass

def cli():
    """Entry point for the CLI application."""
    app()
```

## Configuration

The package uses TOML configuration files with the following structure:

```toml
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "collective.transmute.steps.blocks.process_blocks",
]
do_not_add_drop = ["step_name"]

[paths]
export_prefixes = ["/Plone"]
cleanup = {"/old/path" = "/new/path"}

[paths.filter]
allowed = ["/allowed/path"]
drop = ["/path/to/drop"]

[types]
processor = "default.processor"

[types.Document]
processor = "custom.document_processor"
blocks = [
    {type = "title"},
    {type = "description"},
    {type = "text"}
]
```

## Error Handling

The package provides comprehensive error handling:

- **File Validation**: `check_paths()` validates source and destination paths
- **Step Validation**: `check_steps()` validates pipeline step availability
- **Runtime Errors**: Custom exceptions for configuration and processing errors
- **Logging**: Comprehensive logging throughout the pipeline

## Performance Considerations

- **Async Processing**: All I/O operations use async/await for efficiency
- **Caching**: Step and processor loading is cached for better performance
- **Memory Management**: Items are processed one at a time to manage memory usage
- **Progress Monitoring**: Real-time progress updates for long-running operations 