#!/usr/bin/env python3
"""
Multi-site migration script for collective.transmute.

This script demonstrates how to migrate multiple sites with different
configurations using the collective.transmute package.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

from collective.transmute import pipeline
from collective.transmute import _types as t
from collective.transmute.utils import files as file_utils
from collective.transmute import layout
from collective.transmute.utils import report_time


class MultiSiteMigrator:
    """Handles migration of multiple sites with different configurations."""
    
    def __init__(self, base_config_dir: Path, output_base_dir: Path):
        """Initialize the multi-site migrator.
        
        Args:
            base_config_dir: Directory containing site-specific configurations
            output_base_dir: Base directory for output files
        """
        self.base_config_dir = base_config_dir
        self.output_base_dir = output_base_dir
        self.migration_results = {}
    
    async def migrate_site(
        self, 
        source: Path, 
        destination: Path, 
        config_name: str,
        site_name: str
    ) -> Dict[str, any]:
        """Migrate a single site.
        
        Args:
            source: Source directory path
            destination: Destination directory path
            config_name: Name of the configuration file
            site_name: Name of the site for reporting
            
        Returns:
            Dictionary containing migration results
        """
        
        print(f"Starting migration of {site_name}...")
        
        # Load site-specific configuration
        try:
            import dynaconf
            config_file = self.base_config_dir / f"{config_name}.toml"
            
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
            settings = dynaconf.Dynaconf(
                settings_files=[str(config_file)],
                merge_enabled=True
            )
            
            # Override global settings with site-specific ones
            from collective.transmute.settings import pb_config
            pb_config.update(settings)
            
        except Exception as e:
            print(f"Error loading configuration for {site_name}: {e}")
            return {
                "site_name": site_name,
                "status": "error",
                "error": str(e),
                "processed": 0,
                "exported": 0,
                "dropped": 0
            }
        
        # Get source files
        try:
            src_files = file_utils.get_src_files(source)
        except Exception as e:
            print(f"Error reading source files for {site_name}: {e}")
            return {
                "site_name": site_name,
                "status": "error",
                "error": str(e),
                "processed": 0,
                "exported": 0,
                "dropped": 0
            }
        
        # Create layout
        app_layout = layout.TransmuteLayout(title=f"Migrating {site_name}")
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
        try:
            with layout.live(app_layout, redirect_stderr=False):
                with report_time(f"Migration of {site_name}", consoles):
                    await pipeline(src_files, destination, state, True, consoles)
            
            # Prepare results
            results = {
                "site_name": site_name,
                "status": "success",
                "processed": len(state.seen),
                "exported": dict(state.exported),
                "dropped": dict(state.dropped),
                "total_files": total,
                "metadata_file": str(destination / "metadata.json"),
                "completion_time": datetime.now().isoformat()
            }
            
            print(f"Completed {site_name}: {len(state.seen)} items processed")
            return results
            
        except Exception as e:
            print(f"Error during migration of {site_name}: {e}")
            return {
                "site_name": site_name,
                "status": "error",
                "error": str(e),
                "processed": len(state.seen) if 'state' in locals() else 0,
                "exported": dict(state.exported) if 'state' in locals() else {},
                "dropped": dict(state.dropped) if 'state' in locals() else {},
                "total_files": total if 'total' in locals() else 0
            }
    
    async def migrate_all_sites(self, sites: List[Tuple[str, str, str]]) -> Dict[str, any]:
        """Migrate all specified sites.
        
        Args:
            sites: List of (site_name, source_path, config_name) tuples
            
        Returns:
            Dictionary containing results for all sites
        """
        
        print(f"Starting migration of {len(sites)} sites...")
        
        all_results = {
            "migration_start": datetime.now().isoformat(),
            "total_sites": len(sites),
            "sites": {}
        }
        
        for site_name, source_path, config_name in sites:
            source = Path(source_path)
            destination = self.output_base_dir / site_name
            
            # Create destination directory
            destination.mkdir(parents=True, exist_ok=True)
            
            # Migrate site
            result = await self.migrate_site(source, destination, config_name, site_name)
            all_results["sites"][site_name] = result
        
        all_results["migration_end"] = datetime.now().isoformat()
        
        # Save overall results
        results_file = self.output_base_dir / "migration_results.json"
        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2)
        
        print(f"Migration completed. Results saved to {results_file}")
        return all_results
    
    def generate_summary_report(self, results: Dict[str, any]) -> str:
        """Generate a summary report of the migration.
        
        Args:
            results: Migration results dictionary
            
        Returns:
            Formatted summary report
        """
        
        report_lines = [
            "=" * 60,
            "MULTI-SITE MIGRATION SUMMARY",
            "=" * 60,
            f"Migration Start: {results.get('migration_start', 'Unknown')}",
            f"Migration End: {results.get('migration_end', 'Unknown')}",
            f"Total Sites: {results.get('total_sites', 0)}",
            "",
            "SITE RESULTS:",
            "-" * 30
        ]
        
        total_processed = 0
        total_exported = 0
        total_dropped = 0
        successful_sites = 0
        failed_sites = 0
        
        for site_name, site_result in results.get("sites", {}).items():
            status = site_result.get("status", "unknown")
            processed = site_result.get("processed", 0)
            exported = sum(site_result.get("exported", {}).values())
            dropped = sum(site_result.get("dropped", {}).values())
            
            if status == "success":
                successful_sites += 1
                total_processed += processed
                total_exported += exported
                total_dropped += dropped
            else:
                failed_sites += 1
            
            report_lines.extend([
                f"{site_name}:",
                f"  Status: {status}",
                f"  Processed: {processed}",
                f"  Exported: {exported}",
                f"  Dropped: {dropped}",
                ""
            ])
        
        report_lines.extend([
            "OVERALL SUMMARY:",
            "-" * 30,
            f"Successful Sites: {successful_sites}",
            f"Failed Sites: {failed_sites}",
            f"Total Items Processed: {total_processed}",
            f"Total Items Exported: {total_exported}",
            f"Total Items Dropped: {total_dropped}",
            "=" * 60
        ])
        
        return "\n".join(report_lines)


async def main():
    """Main function for multi-site migration."""
    
    # Configuration
    base_config_dir = Path("configs")
    output_base_dir = Path("output_data")
    source_base_dir = Path("source_data")
    
    # Define sites to migrate
    sites = [
        ("main_site", str(source_base_dir / "main_site"), "main_site_config"),
        ("news_site", str(source_base_dir / "news_site"), "news_site_config"),
        ("events_site", str(source_base_dir / "events_site"), "events_site_config"),
        ("legacy_site", str(source_base_dir / "legacy_site"), "legacy_site_config"),
    ]
    
    # Validate paths
    for site_name, source_path, config_name in sites:
        source = Path(source_path)
        config_file = base_config_dir / f"{config_name}.toml"
        
        if not source.exists():
            print(f"Warning: Source directory not found: {source}")
        
        if not config_file.exists():
            print(f"Warning: Configuration file not found: {config_file}")
    
    # Create output directory
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize migrator
    migrator = MultiSiteMigrator(base_config_dir, output_base_dir)
    
    # Run migration
    try:
        results = await migrator.migrate_all_sites(sites)
        
        # Generate and display summary
        summary = migrator.generate_summary_report(results)
        print(summary)
        
        # Save summary to file
        summary_file = output_base_dir / "migration_summary.txt"
        with open(summary_file, "w") as f:
            f.write(summary)
        
        print(f"Summary saved to {summary_file}")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 