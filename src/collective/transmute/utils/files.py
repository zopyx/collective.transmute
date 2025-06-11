"""
File utility functions for collective.transmute.

This module provides various file operations for reading, writing, and managing
files during the data transformation process. It handles JSON and CSV file
operations, blob file management, and directory operations.
"""

from aiofiles.os import makedirs
from base64 import b64decode
from collections.abc import AsyncGenerator
from collections.abc import Generator
from collections.abc import Iterator
from collective.transmute import _types as t
from collective.transmute import logger
from collective.transmute import settings
from collective.transmute.utils import exportimport as ei_utils
from pathlib import Path

import aiofiles
import csv
import json
import orjson
import shutil


SUFFIX = ".json"


def json_dumps(data: dict | list) -> bytes:
    """Dump data to JSON bytes.
    
    Converts Python data structures to JSON format using orjson for better
    performance, with fallback to standard json module for complex structures.
    
    Args:
        data: Data to convert to JSON
        
    Returns:
        JSON data as bytes
    """
    try:
        # Handles recursion of 255 levels
        response: bytes = orjson.dumps(data, option=orjson.OPT_INDENT_2)
    except orjson.JSONEncodeError:
        response = json.dumps(data, indent=2).encode("utf-8")
    return response


async def json_dump(data: dict | list, path: Path) -> Path:
    """Dump JSON data to a file.
    
    Asynchronously writes JSON data to the specified file path.
    
    Args:
        data: Data to write as JSON
        path: File path to write to
        
    Returns:
        Path to the written file
    """
    async with aiofiles.open(path, "wb") as f:
        await f.write(json_dumps(data))
    return path


async def csv_dump(data: dict | list, header: list[str], path: Path) -> Path:
    """Dump data to CSV file.
    
    Writes data to a CSV file with the specified headers.
    
    Args:
        data: List of dictionaries to write as CSV rows
        header: List of column headers
        path: File path to write to
        
    Returns:
        Path to the written CSV file
    """
    with open(path, "w") as f:
        writer = csv.DictWriter(f, header)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    return path


def check_path(path: Path) -> bool:
    """Check if a path exists.
    
    Args:
        path: Path to check
        
    Returns:
        True if path exists, False otherwise
    """
    path = path.resolve()
    return path.exists()


def check_paths(src: Path, dst: Path) -> bool:
    """Check if source and destination paths exist.
    
    Validates that both source and destination paths exist and are accessible.
    
    Args:
        src: Source path to check
        dst: Destination path to check
        
    Returns:
        True if both paths exist
        
    Raises:
        RuntimeError: If either path does not exist
    """
    if not check_path(src):
        raise RuntimeError(f"{src} does not exist")
    if not check_path(dst):
        raise RuntimeError(f"{dst} does not exist")
    return True


def _sort_content_files(content: list[Path]) -> list[Path]:
    """Sort content files by their numeric names.
    
    Sorts files based on their numeric filename (without extension) to ensure
    proper processing order.
    
    Args:
        content: List of file paths to sort
        
    Returns:
        Sorted list of file paths
    """
    def key(filepath: Path) -> str:
        name, _ = filepath.name.split(".")
        return f"{int(name):07d}"

    result = sorted(content, key=lambda x: key(x))
    return result


def get_src_files(src: Path) -> t.SourceFiles:
    """Get source files from a directory.
    
    Scans a directory for JSON files and categorizes them into metadata
    and content files based on their names.
    
    Args:
        src: Source directory to scan
        
    Returns:
        SourceFiles object containing categorized file paths
    """
    metadata = []
    content = []
    for filepath in src.glob("**/*.json"):
        filepath = filepath.resolve()
        name = filepath.name
        if name.startswith("export_") or name in ("errors.json", "paths.json"):
            metadata.append(filepath)
        else:
            content.append(filepath)
    content = _sort_content_files(content)
    return t.SourceFiles(metadata, content)


async def json_reader(files: Iterator) -> AsyncGenerator[tuple[str, t.PloneItem]]:
    """Read JSON files asynchronously.
    
    Reads multiple JSON files and yields their content as PloneItem objects.
    
    Args:
        files: Iterator of file paths to read
        
    Yields:
        Tuple of (filename, item_data) for each file
    """
    for filepath in files:
        filename = filepath.name
        async with aiofiles.open(filepath, "rb") as f:
            data = await f.read()
            yield filename, orjson.loads(data.decode("utf-8"))


async def export_blob(field: str, blob: dict, content_path: Path, item_id: str) -> dict:
    """Export a blob field to a file.
    
    Decodes base64 blob data and writes it to a file in the appropriate
    directory structure.
    
    Args:
        field: Field name for the blob
        blob: Blob data dictionary containing filename and base64 data
        content_path: Base path for content storage
        item_id: Item ID for fallback filename
        
    Returns:
        Updated blob dictionary with file path information
    """
    await makedirs(content_path / field, exist_ok=True)
    filename = blob["filename"] or item_id
    data = b64decode(blob.pop("data").encode("utf-8"))
    filepath: Path = content_path / field / filename
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(data)
    blob["blob_path"] = f"{filepath.relative_to(content_path.parent)}"
    return blob


async def export_item(item: t.PloneItem, parent_folder: Path) -> t.ItemFiles:
    """Export a Plone item to the destination format.
    
    Writes an item's data and associated blob files to the destination
    directory structure.
    
    Args:
        item: Plone item to export
        parent_folder: Parent directory for the export
        
    Returns:
        ItemFiles object containing data file path and blob file paths
    """
    # Return blobs created here
    blob_files = []
    uid = item.get("UID")
    item_id = item.get("id")
    blobs = item.pop("_blob_files_")
    # TODO: Handle default content for portal
    content_folder = parent_folder / f"{uid}"
    data_path: Path = content_folder / "data.json"
    if blobs:
        for field, value in blobs.items():
            blob = await export_blob(field, value, content_folder, item_id)
            blob_files.append(blob["blob_path"])
            item[field] = blob
    else:
        await makedirs(content_folder, exist_ok=True)
    # Remove internal keys
    item = {key: value for key, value in item.items() if not key.startswith("_")}
    async with aiofiles.open(data_path, "wb") as f:
        await f.write(json_dumps(item))
    return t.ItemFiles(f"{data_path.relative_to(parent_folder)}", blob_files)


async def export_metadata(metadata: t.MetadataInfo, state: t.PipelineState) -> Path:
    """Export metadata to files.
    
    Prepares and writes metadata information to the appropriate files
    in the destination format.
    
    Args:
        metadata: Metadata information to export
        state: Pipeline state for additional context
        
    Returns:
        Path to the main metadata file
    """
    async for data, path in ei_utils.prepare_metadata_file(
        metadata, state, settings.is_debug
    ):
        async with aiofiles.open(path, "wb") as f:
            await f.write(json_dumps(data))
            logger.debug(f"Wrote {path}")
    return path


def remove_data(path: Path, consoles: t.ConsoleArea | None = None):
    """Remove all data inside a given path.
    
    Recursively removes all files and directories within the specified path.
    Useful for cleaning up destination directories before processing.
    
    Args:
        path: Path to clean up
        consoles: Optional console area for progress reporting
    """
    report = consoles.print_log if consoles else logger.debug
    contents: Generator[Path] = path.glob("*")
    for content in contents:
        if content.is_dir():
            shutil.rmtree(content, True)
            report(f" - Removed directory {content}")
        else:
            content.unlink()
            report(f" - Removed file {content}")
