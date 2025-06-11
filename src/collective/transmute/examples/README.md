# Collective Transmute - Migration Examples

This directory contains practical examples of how to use `collective.transmute` for various migration scenarios. Each example demonstrates different aspects of the migration process and common use cases.

## Example Structure

```
examples/
├── README.md                    # This file
├── basic-migration/            # Basic migration example
├── custom-steps/               # Custom transformation steps
├── workflow-migration/         # Workflow-specific migrations
├── content-type-migration/     # Content type transformations
├── path-cleanup/               # Path and ID cleanup examples
└── configuration-examples/     # Configuration examples
```

## Quick Start Examples

### 1. Basic Migration

The simplest form of migration from collective.exportimport to plone.exportimport:

```bash
# Basic migration
python -m collective.transmute transmute run /path/to/source /path/to/destination

# With cleanup and reporting
python -m collective.transmute transmute run \
    /path/to/source \
    /path/to/destination \
    --clean-up \
    --write-report
```

### 2. Generate Source Analysis Report

Before migrating, analyze your source data:

```bash
# Generate comprehensive report
python -m collective.transmute report /path/to/source

# Generate detailed report for specific content types
python -m collective.transmute report /path/to/source --report-types "Document,Folder,News Item"
```

## Migration Scenarios

### Scenario 1: Simple Content Migration

**Use Case**: Migrating a basic Plone site with standard content types.

**Configuration**: `examples/basic-migration/transmute.toml`

```toml
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "collective.transmute.steps.basic_metadata.process_title_description",
    "collective.transmute.steps.blocks.process_blocks",
]

[paths]
export_prefixes = ["/Plone"]
cleanup = {"/old-site" = "/new-site"}

[paths.filter]
allowed = ["/Plone"]
drop = ["/Plone/private", "/Plone/temp"]
```

**Command**:
```bash
cd examples/basic-migration
python -m collective.transmute transmute run source_data output_data --clean-up
```

### Scenario 2: Workflow State Migration

**Use Case**: Migrating content with specific workflow states and ensuring proper state transitions.

**Configuration**: `examples/workflow-migration/transmute.toml`

```toml
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "collective.transmute.steps.review_state.process_review_state",
    "collective.transmute.steps.workflow.process_workflow",
    "collective.transmute.steps.blocks.process_blocks",
]

[workflow]
state_mapping = {
    "private" = "private",
    "published" = "published", 
    "pending" = "pending_review",
    "draft" = "draft"
}

[paths]
export_prefixes = ["/Plone"]
```

**Custom Workflow Step**: `examples/workflow-migration/custom_workflow.py`

```python
"""Custom workflow processing step."""

from collective.transmute import _types as t


async def process_workflow(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process workflow states and transitions."""
    
    # Get current review state
    current_state = item.get("review_state", "private")
    
    # Map old workflow states to new ones
    state_mapping = {
        "private": "private",
        "published": "published",
        "pending": "pending_review",
        "draft": "draft",
        "archived": "archived"
    }
    
    # Update review state
    if current_state in state_mapping:
        item["review_state"] = state_mapping[current_state]
    
    # Handle workflow history
    if workflow_history := item.get("workflow_history", {}):
        # Clean up workflow history for new format
        cleaned_history = {}
        for workflow_id, history in workflow_history.items():
            cleaned_history[workflow_id] = [
                {
                    "action": entry.get("action"),
                    "actor": entry.get("actor"),
                    "comments": entry.get("comments", ""),
                    "review_state": entry.get("review_state"),
                    "time": entry.get("time")
                }
                for entry in history
                if entry.get("action") and entry.get("review_state")
            ]
        item["workflow_history"] = cleaned_history
    
    yield item
```

### Scenario 3: Content Type Transformation

**Use Case**: Migrating custom content types and transforming them to standard types.

**Configuration**: `examples/content-type-migration/transmute.toml`

```toml
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "collective.transmute.steps.portal_type.process_portal_type",
    "collective.transmute.steps.blocks.process_blocks",
]

[types]
processor = "collective.transmute.utils.default_processor"

[types.CustomNewsItem]
processor = "examples.content_type_migration.custom_news_processor"
blocks = [
    {type = "title"},
    {type = "description"},
    {type = "text"},
    {type = "image"}
]

[portal_type.mapping]
CustomNewsItem = "News Item"
CustomEvent = "Event"
LegacyDocument = "Document"
```

**Custom Type Processor**: `examples/content-type-migration/custom_news_processor.py`

```python
"""Custom processor for News Item content type."""

from collective.transmute import _types as t


async def custom_news_processor(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process custom news items."""
    
    # Transform custom fields to standard fields
    if custom_title := item.pop("custom_title", None):
        item["title"] = custom_title
    
    if custom_body := item.pop("custom_body", None):
        item["text"] = {"data": custom_body, "content-type": "text/html"}
    
    # Handle custom image field
    if custom_image := item.pop("custom_image", None):
        item["image"] = custom_image
    
    # Set standard metadata
    item["@type"] = "News Item"
    item["effective"] = item.get("effective") or item.get("created")
    item["expires"] = item.get("expires")
    
    yield item
```

### Scenario 4: Path and ID Cleanup

**Use Case**: Cleaning up messy paths and IDs during migration.

**Configuration**: `examples/path-cleanup/transmute.toml`

```toml
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "collective.transmute.steps.paths.process_paths",
    "collective.transmute.steps.blocks.process_blocks",
]

[paths]
export_prefixes = ["/Plone", "/old-site"]
cleanup = {
    "/old-site" = "/new-site",
    "/legacy-content" = "/content",
    "/temp" = "",
    "/draft" = ""
}

[paths.filter]
allowed = ["/new-site", "/content"]
drop = ["/new-site/private", "/new-site/temp", "/content/draft"]
```

### Scenario 5: Complex Block Migration

**Use Case**: Migrating complex content with custom blocks and layouts.

**Configuration**: `examples/complex-blocks/transmute.toml`

```toml
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "collective.transmute.steps.blocks.process_blocks",
    "examples.complex_blocks.custom_block_processor",
]

[types.Document]
blocks = [
    {type = "title"},
    {type = "description"},
    {type = "text"},
    {type = "image"},
    {type = "listing"}
]

[types.Folder]
blocks = [
    {type = "title"},
    {type = "description"},
    {type = "listing"}
]
```

**Custom Block Processor**: `examples/complex-blocks/custom_block_processor.py`

```python
"""Custom block processor for complex content."""

from collective.transmute import _types as t


async def custom_block_processor(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process complex blocks and layouts."""
    
    # Handle custom layout blocks
    if custom_layout := item.pop("custom_layout", None):
        blocks = item.get("blocks", {})
        
        # Convert custom layout to standard blocks
        for block_id, block_data in custom_layout.items():
            if block_data.get("type") == "custom_gallery":
                # Transform custom gallery to image gallery block
                blocks[block_id] = {
                    "@type": "imageGallery",
                    "images": block_data.get("images", []),
                    "styles": block_data.get("styles", {})
                }
            elif block_data.get("type") == "custom_listing":
                # Transform custom listing to standard listing block
                blocks[block_id] = {
                    "@type": "listing",
                    "headline": block_data.get("headline", ""),
                    "variation": block_data.get("variation", "summary"),
                    "styles": block_data.get("styles", {})
                }
        
        item["blocks"] = blocks
    
    # Handle legacy text content
    if legacy_text := item.pop("legacy_text", None):
        # Convert legacy text to blocks format
        if "blocks" not in item:
            item["blocks"] = {}
        
        item["blocks"]["text-1"] = {
            "@type": "text",
            "text": {"data": legacy_text, "content-type": "text/html"}
        }
    
    yield item
```

## Advanced Examples

### Example 1: Multi-Site Migration

**Use Case**: Migrating multiple sites with different configurations.

**Script**: `examples/multi-site/migrate_all.py`

```python
#!/usr/bin/env python3
"""Multi-site migration script."""

import asyncio
from pathlib import Path
from collective.transmute import pipeline
from collective.transmute import _types as t
from collective.transmute.utils import files as file_utils
from collective.transmute import layout


async def migrate_site(source: Path, destination: Path, config_name: str):
    """Migrate a single site."""
    
    # Load site-specific configuration
    import dynaconf
    settings = dynaconf.Dynaconf(
        settings_files=[f"configs/{config_name}.toml"],
        merge_enabled=True
    )
    
    # Get source files
    src_files = file_utils.get_src_files(source)
    
    # Create layout
    app_layout = layout.TransmuteLayout(title=f"Migrating {source.name}")
    consoles = app_layout.consoles
    
    # Initialize state
    total = len(src_files.content)
    state = t.PipelineState(
        total=total,
        processed=0,
        exported=t.defaultdict(int),
        dropped=t.defaultdict(int),
        progress=app_layout.progress,
    )
    
    # Run migration
    with layout.live(app_layout, redirect_stderr=False):
        await pipeline(src_files, destination, state, True, consoles)
    
    return state


async def main():
    """Migrate all sites."""
    
    sites = [
        ("site1", "site1_config"),
        ("site2", "site2_config"),
        ("site3", "site3_config"),
    ]
    
    for site_name, config_name in sites:
        source = Path(f"source_data/{site_name}")
        destination = Path(f"output_data/{site_name}")
        
        print(f"Migrating {site_name}...")
        state = await migrate_site(source, destination, config_name)
        print(f"Completed {site_name}: {len(state.seen)} items processed")


if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Incremental Migration

**Use Case**: Migrating content incrementally to avoid downtime.

**Script**: `examples/incremental/incremental_migration.py`

```python
#!/usr/bin/env python3
"""Incremental migration script."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collective.transmute import pipeline
from collective.transmute import _types as t
from collective.transmute.utils import files as file_utils
from collective.transmute import layout


class IncrementalMigrator:
    """Handles incremental migrations."""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.migrated_items = self._load_state()
    
    def _load_state(self) -> set:
        """Load previously migrated items."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                data = json.load(f)
                return set(data.get("migrated_items", []))
        return set()
    
    def _save_state(self, items: set):
        """Save migration state."""
        data = {
            "migrated_items": list(items),
            "last_update": datetime.now().isoformat()
        }
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)
    
    async def migrate_incremental(self, source: Path, destination: Path):
        """Migrate only new or modified items."""
        
        # Get all source files
        src_files = file_utils.get_src_files(source)
        
        # Filter for new/modified items
        new_items = []
        for file_path in src_files.content:
            item_uid = file_path.stem  # Assuming filename is UID
            if item_uid not in self.migrated_items:
                new_items.append(file_path)
        
        if not new_items:
            print("No new items to migrate")
            return
        
        print(f"Found {len(new_items)} new items to migrate")
        
        # Create filtered source files
        filtered_src_files = t.SourceFiles(
            metadata=src_files.metadata,
            content=new_items
        )
        
        # Run migration
        app_layout = layout.TransmuteLayout(title="Incremental Migration")
        consoles = app_layout.consoles
        
        state = t.PipelineState(
            total=len(new_items),
            processed=0,
            exported=t.defaultdict(int),
            dropped=t.defaultdict(int),
            progress=app_layout.progress,
        )
        
        with layout.live(app_layout, redirect_stderr=False):
            await pipeline(filtered_src_files, destination, state, False, consoles)
        
        # Update state
        self.migrated_items.update(state.seen)
        self._save_state(self.migrated_items)
        
        print(f"Migrated {len(state.seen)} new items")


async def main():
    """Run incremental migration."""
    
    source = Path("source_data")
    destination = Path("output_data")
    state_file = Path("migration_state.json")
    
    migrator = IncrementalMigrator(state_file)
    await migrator.migrate_incremental(source, destination)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Testing Your Migration

### 1. Dry Run

Before running a full migration, test with a subset:

```bash
# Create a test subset
mkdir test_source
cp source_data/*.json test_source/  # Copy first few files

# Run test migration
python -m collective.transmute transmute run test_source test_output --write-report
```

### 2. Validate Results

```bash
# Generate report on migrated data
python -m collective.transmute report test_output

# Compare source and destination
python -m collective.transmute report source_data --report-types "Document,Folder"
python -m collective.transmute report test_output --report-types "Document,Folder"
```

### 3. Check for Errors

```bash
# Run sanity checks
python -m collective.transmute sanity

# Check configuration
python -m collective.transmute settings
```

## Best Practices

1. **Always backup** your source data before migration
2. **Test with a subset** before full migration
3. **Generate reports** to understand your data structure
4. **Use incremental migration** for large datasets
5. **Monitor progress** with the rich UI
6. **Validate results** after migration
7. **Keep configuration files** for reproducibility

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Install required packages
2. **File permissions**: Check read/write permissions
3. **Memory issues**: Process in smaller batches
4. **Configuration errors**: Validate TOML syntax

### Debug Mode

```bash
export COLLECTIVE_TRANSMUTE_DEBUG=true
python -m collective.transmute transmute run source dest
```

### Getting Help

- Check the main README.md for detailed documentation
- Review the API.md for technical reference
- Run `python -m collective.transmute --help` for CLI options
- Enable debug mode for detailed logging 