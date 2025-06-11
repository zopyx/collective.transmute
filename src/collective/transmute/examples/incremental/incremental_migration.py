#!/usr/bin/env python3
"""
Incremental migration script for collective.transmute.

This script demonstrates how to migrate content incrementally to avoid
downtime and handle large datasets efficiently.
"""

import json
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional
from dataclasses import dataclass, asdict

from collective.transmute import pipeline
from collective.transmute import _types as t
from collective.transmute.utils import files as file_utils
from collective.transmute import layout
from collective.transmute.utils import report_time


@dataclass
class MigrationState:
    """Represents the state of an incremental migration."""
    
    migrated_items: Set[str]
    last_update: str
    total_processed: int
    total_exported: int
    total_dropped: int
    migration_start: str
    last_sync_time: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "migrated_items": list(self.migrated_items),
            "last_update": self.last_update,
            "total_processed": self.total_processed,
            "total_exported": self.total_exported,
            "total_dropped": self.total_dropped,
            "migration_start": self.migration_start,
            "last_sync_time": self.last_sync_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MigrationState':
        """Create from dictionary."""
        return cls(
            migrated_items=set(data.get("migrated_items", [])),
            last_update=data.get("last_update", datetime.now().isoformat()),
            total_processed=data.get("total_processed", 0),
            total_exported=data.get("total_exported", 0),
            total_dropped=data.get("total_dropped", 0),
            migration_start=data.get("migration_start", datetime.now().isoformat()),
            last_sync_time=data.get("last_sync_time")
        )


class IncrementalMigrator:
    """Handles incremental migrations with state tracking."""
    
    def __init__(self, state_file: Path, batch_size: int = 100):
        """Initialize the incremental migrator.
        
        Args:
            state_file: Path to the state file for tracking progress
            batch_size: Number of items to process in each batch
        """
        self.state_file = state_file
        self.batch_size = batch_size
        self.state = self._load_state()
    
    def _load_state(self) -> MigrationState:
        """Load migration state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                    return MigrationState.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load state file: {e}")
        
        # Create new state
        return MigrationState(
            migrated_items=set(),
            last_update=datetime.now().isoformat(),
            total_processed=0,
            total_exported=0,
            total_dropped=0,
            migration_start=datetime.now().isoformat()
        )
    
    def _save_state(self):
        """Save current state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
    
    def _get_item_hash(self, file_path: Path) -> str:
        """Generate a hash for an item based on file path and modification time."""
        try:
            stat = file_path.stat()
            # Use filename and modification time for hash
            content = f"{file_path.name}:{stat.st_mtime}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            # Fallback to filename only
            return hashlib.md5(file_path.name.encode()).hexdigest()
    
    def _is_item_modified(self, file_path: Path) -> bool:
        """Check if an item has been modified since last migration."""
        item_hash = self._get_item_hash(file_path)
        return item_hash not in self.state.migrated_items
    
    async def migrate_incremental(
        self, 
        source: Path, 
        destination: Path,
        force_full: bool = False
    ) -> Dict[str, any]:
        """Migrate only new or modified items.
        
        Args:
            source: Source directory path
            destination: Destination directory path
            force_full: Force full migration ignoring state
            
        Returns:
            Dictionary containing migration results
        """
        
        print(f"Starting incremental migration from {source} to {destination}")
        
        # Get all source files
        try:
            src_files = file_utils.get_src_files(source)
        except Exception as e:
            print(f"Error reading source files: {e}")
            return {"status": "error", "error": str(e)}
        
        # Filter for new/modified items
        new_items = []
        modified_items = []
        
        for file_path in src_files.content:
            if force_full or self._is_item_modified(file_path):
                new_items.append(file_path)
                if not force_full:
                    modified_items.append(file_path)
        
        if not new_items:
            print("No new or modified items to migrate")
            return {
                "status": "success",
                "message": "No new items to migrate",
                "processed": 0,
                "exported": 0,
                "dropped": 0
            }
        
        print(f"Found {len(new_items)} items to migrate ({len(modified_items)} modified)")
        
        # Process in batches
        total_processed = 0
        total_exported = 0
        total_dropped = 0
        
        for i in range(0, len(new_items), self.batch_size):
            batch = new_items[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(new_items) + self.batch_size - 1) // self.batch_size
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
            
            # Create filtered source files for this batch
            batch_src_files = t.SourceFiles(
                metadata=src_files.metadata,
                content=batch
            )
            
            # Run migration for this batch
            batch_result = await self._migrate_batch(batch_src_files, destination, batch_num)
            
            if batch_result["status"] == "error":
                return batch_result
            
            total_processed += batch_result["processed"]
            total_exported += batch_result["exported"]
            total_dropped += batch_result["dropped"]
            
            # Update state after each batch
            for file_path in batch:
                item_hash = self._get_item_hash(file_path)
                self.state.migrated_items.add(item_hash)
            
            self.state.total_processed = total_processed
            self.state.total_exported = total_exported
            self.state.total_dropped = total_dropped
            self.state.last_update = datetime.now().isoformat()
            
            # Save state after each batch
            self._save_state()
        
        print(f"Incremental migration completed: {total_processed} items processed")
        
        return {
            "status": "success",
            "processed": total_processed,
            "exported": total_exported,
            "dropped": total_dropped,
            "new_items": len(new_items),
            "modified_items": len(modified_items)
        }
    
    async def _migrate_batch(
        self, 
        src_files: t.SourceFiles, 
        destination: Path, 
        batch_num: int
    ) -> Dict[str, any]:
        """Migrate a single batch of items.
        
        Args:
            src_files: Source files for this batch
            destination: Destination directory
            batch_num: Batch number for logging
            
        Returns:
            Dictionary containing batch results
        """
        
        # Create layout
        app_layout = layout.TransmuteLayout(title=f"Batch {batch_num}")
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
        
        try:
            with layout.live(app_layout, redirect_stderr=False):
                with report_time(f"Batch {batch_num}", consoles):
                    await pipeline(src_files, destination, state, False, consoles)
            
            return {
                "status": "success",
                "processed": len(state.seen),
                "exported": sum(state.exported.values()),
                "dropped": sum(state.dropped.values())
            }
            
        except Exception as e:
            print(f"Error in batch {batch_num}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processed": len(state.seen) if 'state' in locals() else 0,
                "exported": sum(state.exported.values()) if 'state' in locals() else 0,
                "dropped": sum(state.dropped.values()) if 'state' in locals() else 0
            }
    
    def get_migration_stats(self) -> Dict[str, any]:
        """Get current migration statistics.
        
        Returns:
            Dictionary containing migration statistics
        """
        return {
            "migrated_items_count": len(self.state.migrated_items),
            "total_processed": self.state.total_processed,
            "total_exported": self.state.total_exported,
            "total_dropped": self.state.total_dropped,
            "migration_start": self.state.migration_start,
            "last_update": self.state.last_update,
            "last_sync_time": self.state.last_sync_time
        }
    
    def reset_migration_state(self):
        """Reset migration state (start fresh)."""
        self.state = MigrationState(
            migrated_items=set(),
            last_update=datetime.now().isoformat(),
            total_processed=0,
            total_exported=0,
            total_dropped=0,
            migration_start=datetime.now().isoformat()
        )
        self._save_state()
        print("Migration state reset")


async def main():
    """Main function for incremental migration."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Incremental migration script")
    parser.add_argument("source", help="Source directory path")
    parser.add_argument("destination", help="Destination directory path")
    parser.add_argument("--state-file", default="migration_state.json", 
                       help="State file path (default: migration_state.json)")
    parser.add_argument("--batch-size", type=int, default=100,
                       help="Batch size for processing (default: 100)")
    parser.add_argument("--force-full", action="store_true",
                       help="Force full migration ignoring state")
    parser.add_argument("--reset", action="store_true",
                       help="Reset migration state and start fresh")
    parser.add_argument("--stats", action="store_true",
                       help="Show migration statistics and exit")
    
    args = parser.parse_args()
    
    source = Path(args.source)
    destination = Path(args.destination)
    state_file = Path(args.state_file)
    
    # Validate paths
    if not source.exists():
        print(f"Error: Source directory does not exist: {source}")
        return 1
    
    # Create destination directory
    destination.mkdir(parents=True, exist_ok=True)
    
    # Initialize migrator
    migrator = IncrementalMigrator(state_file, args.batch_size)
    
    # Handle special commands
    if args.stats:
        stats = migrator.get_migration_stats()
        print("Migration Statistics:")
        print(f"  Migrated Items: {stats['migrated_items_count']}")
        print(f"  Total Processed: {stats['total_processed']}")
        print(f"  Total Exported: {stats['total_exported']}")
        print(f"  Total Dropped: {stats['total_dropped']}")
        print(f"  Migration Start: {stats['migration_start']}")
        print(f"  Last Update: {stats['last_update']}")
        return 0
    
    if args.reset:
        migrator.reset_migration_state()
        print("Migration state reset. Ready for fresh migration.")
        return 0
    
    # Run migration
    try:
        result = await migrator.migrate_incremental(source, destination, args.force_full)
        
        if result["status"] == "success":
            print("Migration completed successfully!")
            print(f"  Processed: {result['processed']}")
            print(f"  Exported: {result['exported']}")
            print(f"  Dropped: {result['dropped']}")
            if "new_items" in result:
                print(f"  New Items: {result['new_items']}")
                print(f"  Modified Items: {result['modified_items']}")
            return 0
        else:
            print(f"Migration failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Migration failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main())) 