# Collective Transmute

A comprehensive data transformation utility for converting Plone content from `collective.exportimport` format to `plone.exportimport` format.

## Overview

Collective Transmute is a powerful tool designed to facilitate the migration of Plone content from legacy export formats to modern import formats. It provides a modular, step-based processing pipeline with rich UI monitoring and detailed reporting capabilities.

## Features

- **Modular Pipeline**: Step-based processing system for flexible data transformation
- **Rich UI**: Beautiful terminal interface with real-time progress monitoring
- **Comprehensive Reporting**: Detailed CSV reports of transformation results
- **Configurable**: TOML-based configuration for customizing transformation rules
- **Type-Specific Processing**: Custom processors for different content types
- **Blob Management**: Automatic handling of file attachments and binary data
- **Path Transformation**: Intelligent ID and path cleanup and transformation

## Installation

```bash
pip install collective.transmute
```

## Quick Start

### Basic Usage

Transform data from a source directory to a destination directory:

```bash
python -m collective.transmute transmute run /path/to/source /path/to/destination
```

### With Options

```bash
python -m collective.transmute transmute run \
    /path/to/source \
    /path/to/destination \
    --write-report \
    --clean-up \
    --ui
```

## Command Line Interface

The package provides several commands for different operations:

### Transmute Command

The main command for data transformation:

```bash
python -m collective.transmute transmute run <source> <destination> [OPTIONS]
```

**Arguments:**
- `source`: Source directory containing collective.exportimport data
- `destination`: Destination directory for plone.exportimport output

**Options:**
- `--write-report`: Generate a detailed CSV report of transformations
- `--clean-up`: Remove existing content in destination before processing
- `--ui / --no-ui`: Enable/disable rich terminal UI (default: enabled)

### Report Command

Generate reports about source data:

```bash
python -m collective.transmute report <source> [OPTIONS]
```

**Arguments:**
- `source`: Source directory to analyze

**Options:**
- `--ui / --no-ui`: Enable/disable rich terminal UI

### Settings Command

Manage configuration settings:

```bash
python -m collective.transmute settings [OPTIONS]
```

### Sanity Command

Run sanity checks on the configuration:

```bash
python -m collective.transmute sanity [OPTIONS]
```

## Configuration

The package uses TOML configuration files for customizing transformation behavior. The default configuration is located in `settings/default.toml`.

### Key Configuration Sections

#### Pipeline Configuration

```toml
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "collective.transmute.steps.blocks.process_blocks",
    # Add more steps as needed
]
do_not_add_drop = ["step_name"]
```

#### Path Configuration

```toml
[paths]
export_prefixes = ["/Plone"]
cleanup = {"/old/path" = "/new/path"}

[paths.filter]
allowed = ["/allowed/path"]
drop = ["/path/to/drop"]
```

#### Type Configuration

```toml
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

## Architecture

### Core Components

1. **Pipeline**: Main processing engine that orchestrates transformation steps
2. **Steps**: Modular transformation functions for specific data types
3. **Utils**: Helper functions for file operations, reporting, and data processing
4. **Layout**: Rich UI components for progress monitoring and reporting
5. **Settings**: Configuration management using TOML files
6. **Commands**: CLI interface for various operations

### Data Flow

1. **Source Discovery**: Scan source directory for JSON files
2. **File Categorization**: Separate metadata and content files
3. **Pipeline Processing**: Apply transformation steps to each item
4. **Blob Export**: Handle file attachments and binary data
5. **Metadata Generation**: Create final metadata files
6. **Reporting**: Generate transformation reports

### Pipeline Steps

The transformation pipeline consists of several steps that process items sequentially:

- **ID Processing**: Clean up item IDs and paths
- **Block Processing**: Convert content to Volto blocks format
- **Type Transformation**: Apply type-specific transformations
- **Metadata Updates**: Update item metadata
- **Custom Steps**: User-defined transformation steps

## Creating Custom Steps

You can create custom transformation steps by implementing async generator functions:

```python
async def custom_step(item: dict, metadata: dict):
    """Custom transformation step."""
    # Transform the item
    item["custom_field"] = "transformed_value"
    yield item
```

Register your custom step in the configuration:

```toml
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "my_module.custom_step"
]
```

## File Structure

The package organizes files into logical directories:

```
collective/transmute/
├── __init__.py          # Package initialization
├── _types.py           # Type definitions and dataclasses
├── cli.py              # Command line interface
├── about.py            # Version information
├── commands/           # CLI command implementations
│   ├── transmute.py    # Main transformation command
│   ├── report.py       # Reporting command
│   ├── settings.py     # Settings management
│   └── sanity.py       # Sanity checks
├── pipeline/           # Core processing engine
│   └── __init__.py     # Pipeline implementation
├── steps/              # Transformation steps
│   ├── blocks.py       # Block processing
│   ├── ids.py          # ID processing
│   ├── paths.py        # Path processing
│   └── ...             # Other step modules
├── utils/              # Utility functions
│   ├── __init__.py     # General utilities
│   ├── files.py        # File operations
│   └── ...             # Other utility modules
├── layout/             # UI components
│   └── __init__.py     # Rich UI layouts
└── settings/           # Configuration
    ├── __init__.py     # Settings management
    └── default.toml    # Default configuration
```

## Error Handling

The package provides comprehensive error handling and logging:

- **File Validation**: Checks for required files and directories
- **Step Validation**: Validates pipeline step availability
- **Progress Tracking**: Monitors processing progress and reports issues
- **Detailed Logging**: Logs all operations for debugging

## Performance Considerations

- **Async Processing**: Uses async/await for efficient I/O operations
- **Caching**: Caches step and processor loading for better performance
- **Progress Monitoring**: Real-time progress updates for long-running operations
- **Memory Management**: Processes items one at a time to manage memory usage

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure all required packages are installed
2. **Configuration Errors**: Check TOML configuration syntax
3. **File Permissions**: Verify read/write permissions for source and destination
4. **Memory Issues**: For large datasets, consider processing in batches

### Debug Mode

Enable debug mode for detailed logging:

```bash
export COLLECTIVE_TRANSMUTE_DEBUG=true
python -m collective.transmute transmute run source dest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Check the documentation
- Review the configuration examples
- Open an issue on GitHub
- Contact the development team

## Version History

- **1.0.0a0**: Initial alpha release with core functionality 