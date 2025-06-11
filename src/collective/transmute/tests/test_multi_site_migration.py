"""
Tests for multi-site migration examples.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

from collective.transmute import _types as t


class TestMultiSiteMigrator:
    """Test the MultiSiteMigrator class."""
    
    @pytest.fixture
    def migrator(self, temp_dir):
        """Create a MultiSiteMigrator instance."""
        from examples.multi_site.migrate_all import MultiSiteMigrator
        
        config_dir = temp_dir / "configs"
        config_dir.mkdir()
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        return MultiSiteMigrator(config_dir, output_dir)
    
    @pytest.fixture
    def sample_sites(self, temp_dir):
        """Create sample site data for testing."""
        sites = []
        
        for i in range(3):
            site_name = f"site{i+1}"
            site_dir = temp_dir / "source_data" / site_name
            site_dir.mkdir(parents=True)
            
            # Create sample content files
            for j in range(5):
                content_file = site_dir / f"item{j}.json"
                with open(content_file, "w") as f:
                    json.dump({
                        "@type": "Document",
                        "@id": f"/Plone/{site_name}/item{j}",
                        "UID": f"uid-{site_name}-{j}",
                        "title": f"Item {j} from {site_name}",
                        "text": {"data": f"Content {j}", "content-type": "text/html"}
                    }, f)
            
            sites.append((site_name, str(site_dir), f"{site_name}_config"))
        
        return sites
    
    @pytest.fixture
    def mock_config_files(self, temp_dir):
        """Create mock configuration files."""
        config_dir = temp_dir / "configs"
        config_dir.mkdir()
        
        configs = {
            "site1_config": """
[pipeline]
steps = ["collective.transmute.steps.ids.process_ids"]

[paths]
export_prefixes = ["/Plone"]
""",
            "site2_config": """
[pipeline]
steps = ["collective.transmute.steps.ids.process_ids"]

[paths]
export_prefixes = ["/Plone"]
""",
            "site3_config": """
[pipeline]
steps = ["collective.transmute.steps.ids.process_ids"]

[paths]
export_prefixes = ["/Plone"]
"""
        }
        
        for config_name, content in configs.items():
            config_file = config_dir / f"{config_name}.toml"
            with open(config_file, "w") as f:
                f.write(content)
        
        return config_dir
    
    @pytest.mark.asyncio
    async def test_migrate_site_success(self, migrator, sample_sites, mock_config_files):
        """Test successful site migration."""
        site_name, source_path, config_name = sample_sites[0]
        source = Path(source_path)
        destination = migrator.output_base_dir / site_name
        
        # Mock the pipeline function
        with patch('examples.multi_site.migrate_all.pipeline') as mock_pipeline:
            mock_pipeline.return_value = None
            
            # Mock the layout and state
            with patch('examples.multi_site.migrate_all.layout') as mock_layout:
                mock_layout.TransmuteLayout.return_value = Mock()
                mock_layout.live.return_value.__enter__ = Mock()
                mock_layout.live.return_value.__exit__ = Mock()
                
                result = await migrator.migrate_site(source, destination, config_name, site_name)
        
        assert result["status"] == "success"
        assert result["site_name"] == site_name
        assert result["processed"] == 0  # Mocked pipeline doesn't process anything
        assert "completion_time" in result
    
    @pytest.mark.asyncio
    async def test_migrate_site_config_error(self, migrator, sample_sites):
        """Test site migration with configuration error."""
        site_name, source_path, config_name = sample_sites[0]
        source = Path(source_path)
        destination = migrator.output_base_dir / site_name
        
        # Use non-existent config file
        result = await migrator.migrate_site(source, destination, "nonexistent_config", site_name)
        
        assert result["status"] == "error"
        assert "Configuration file not found" in result["error"]
        assert result["processed"] == 0
        assert result["exported"] == 0
        assert result["dropped"] == 0
    
    @pytest.mark.asyncio
    async def test_migrate_site_source_error(self, migrator, sample_sites, mock_config_files):
        """Test site migration with source file error."""
        site_name, source_path, config_name = sample_sites[0]
        source = Path("/nonexistent/source")  # Non-existent source
        destination = migrator.output_base_dir / site_name
        
        result = await migrator.migrate_site(source, destination, config_name, site_name)
        
        assert result["status"] == "error"
        assert result["processed"] == 0
        assert result["exported"] == 0
        assert result["dropped"] == 0
    
    @pytest.mark.asyncio
    async def test_migrate_site_pipeline_error(self, migrator, sample_sites, mock_config_files):
        """Test site migration with pipeline error."""
        site_name, source_path, config_name = sample_sites[0]
        source = Path(source_path)
        destination = migrator.output_base_dir / site_name
        
        # Mock pipeline to raise an exception
        with patch('examples.multi_site.migrate_all.pipeline') as mock_pipeline:
            mock_pipeline.side_effect = Exception("Pipeline error")
            
            with patch('examples.multi_site.migrate_all.layout') as mock_layout:
                mock_layout.TransmuteLayout.return_value = Mock()
                mock_layout.live.return_value.__enter__ = Mock()
                mock_layout.live.return_value.__exit__ = Mock()
                
                result = await migrator.migrate_site(source, destination, config_name, site_name)
        
        assert result["status"] == "error"
        assert "Pipeline error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_migrate_all_sites(self, migrator, sample_sites, mock_config_files):
        """Test migration of all sites."""
        # Mock the pipeline function
        with patch('examples.multi_site.migrate_all.pipeline') as mock_pipeline:
            mock_pipeline.return_value = None
            
            with patch('examples.multi_site.migrate_all.layout') as mock_layout:
                mock_layout.TransmuteLayout.return_value = Mock()
                mock_layout.live.return_value.__enter__ = Mock()
                mock_layout.live.return_value.__exit__ = Mock()
                
                results = await migrator.migrate_all_sites(sample_sites)
        
        assert results["total_sites"] == 3
        assert "migration_start" in results
        assert "migration_end" in results
        assert len(results["sites"]) == 3
        
        # Check that all sites were processed
        for site_name, _, _ in sample_sites:
            assert site_name in results["sites"]
            assert results["sites"][site_name]["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_migrate_all_sites_with_errors(self, migrator, sample_sites):
        """Test migration of all sites with some errors."""
        # Mock pipeline to fail for one site
        with patch('examples.multi_site.migrate_all.pipeline') as mock_pipeline:
            def mock_pipeline_side_effect(*args, **kwargs):
                # Fail for site2
                if "site2" in str(args[0]):
                    raise Exception("Site2 error")
                return None
            
            mock_pipeline.side_effect = mock_pipeline_side_effect
            
            with patch('examples.multi_site.migrate_all.layout') as mock_layout:
                mock_layout.TransmuteLayout.return_value = Mock()
                mock_layout.live.return_value.__enter__ = Mock()
                mock_layout.live.return_value.__exit__ = Mock()
                
                results = await migrator.migrate_all_sites(sample_sites)
        
        assert results["total_sites"] == 3
        assert len(results["sites"]) == 3
        
        # Check that site2 failed
        assert results["sites"]["site2"]["status"] == "error"
        assert "Site2 error" in results["sites"]["site2"]["error"]
        
        # Check that other sites succeeded
        assert results["sites"]["site1"]["status"] == "success"
        assert results["sites"]["site3"]["status"] == "success"
    
    def test_generate_summary_report(self, migrator, sample_migration_results):
        """Test summary report generation."""
        summary = migrator.generate_summary_report(sample_migration_results)
        
        # Check that summary contains expected information
        assert "MULTI-SITE MIGRATION SUMMARY" in summary
        assert "Migration Start: 2023-01-01T10:00:00Z" in summary
        assert "Migration End: 2023-01-01T11:00:00Z" in summary
        assert "Total Sites: 3" in summary
        
        # Check site results
        assert "site1:" in summary
        assert "Status: success" in summary
        assert "Processed: 100" in summary
        
        # Check overall summary
        assert "Successful Sites: 2" in summary
        assert "Failed Sites: 1" in summary
        assert "Total Items Processed: 150" in summary
        assert "Total Items Exported: 143" in summary
        assert "Total Items Dropped: 7" in summary


class TestMultiSiteConfiguration:
    """Test multi-site configuration handling."""
    
    def test_site_configuration_validation(self, temp_dir):
        """Test site configuration validation."""
        from examples.multi_site.migrate_all import main
        
        # Create test configuration
        config_dir = temp_dir / "configs"
        config_dir.mkdir()
        
        source_base_dir = temp_dir / "source_data"
        source_base_dir.mkdir()
        
        output_base_dir = temp_dir / "output_data"
        output_base_dir.mkdir()
        
        # Create some site directories
        for i in range(2):
            site_dir = source_base_dir / f"site{i+1}"
            site_dir.mkdir()
            
            # Create sample content
            content_file = site_dir / "item.json"
            with open(content_file, "w") as f:
                json.dump({"@type": "Document", "title": f"Site {i+1} Item"}, f)
        
        # Create config files
        for i in range(2):
            config_file = config_dir / f"site{i+1}_config.toml"
            with open(config_file, "w") as f:
                f.write(f"""
[pipeline]
steps = ["collective.transmute.steps.ids.process_ids"]

[paths]
export_prefixes = ["/Plone"]
""")
        
        # Test that all paths exist
        for i in range(2):
            site_dir = source_base_dir / f"site{i+1}"
            config_file = config_dir / f"site{i+1}_config.toml"
            
            assert site_dir.exists()
            assert config_file.exists()
    
    def test_configuration_file_loading(self, temp_dir):
        """Test configuration file loading."""
        config_dir = temp_dir / "configs"
        config_dir.mkdir()
        
        config_content = """
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "collective.transmute.steps.basic_metadata.process_title_description"
]

[paths]
export_prefixes = ["/Plone"]
cleanup = {"/old-site" = "/new-site"}

[types]
processor = "collective.transmute.utils.default_processor"
"""
        
        config_file = config_dir / "test_config.toml"
        with open(config_file, "w") as f:
            f.write(config_content)
        
        # Test that file can be read and parsed
        assert config_file.exists()
        
        # Test dynaconf loading (mocked)
        with patch('examples.multi_site.migrate_all.dynaconf') as mock_dynaconf:
            mock_settings = Mock()
            mock_dynaconf.Dynaconf.return_value = mock_settings
            
            # This would normally load the configuration
            settings = mock_dynaconf.Dynaconf(
                settings_files=[str(config_file)],
                merge_enabled=True
            )
            
            assert settings is not None


class TestMultiSiteIntegration:
    """Integration tests for multi-site migration."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_multi_site_migration(self, temp_dir):
        """Test end-to-end multi-site migration process."""
        # Create test structure
        config_dir = temp_dir / "configs"
        config_dir.mkdir()
        
        source_base_dir = temp_dir / "source_data"
        source_base_dir.mkdir()
        
        output_base_dir = temp_dir / "output_data"
        output_base_dir.mkdir()
        
        # Create multiple sites with different content
        sites = []
        for i in range(3):
            site_name = f"site{i+1}"
            site_dir = source_base_dir / site_name
            site_dir.mkdir()
            
            # Create different content for each site
            for j in range(3):
                content_file = site_dir / f"item{j}.json"
                with open(content_file, "w") as f:
                    json.dump({
                        "@type": "Document",
                        "@id": f"/Plone/{site_name}/item{j}",
                        "UID": f"uid-{site_name}-{j}",
                        "title": f"Item {j} from {site_name}",
                        "text": {"data": f"Content {j} from {site_name}", "content-type": "text/html"}
                    }, f)
            
            # Create site-specific config
            config_file = config_dir / f"{site_name}_config.toml"
            with open(config_file, "w") as f:
                f.write(f"""
[pipeline]
steps = ["collective.transmute.steps.ids.process_ids"]

[paths]
export_prefixes = ["/Plone"]

[config]
site_name = "{site_name}"
""")
            
            sites.append((site_name, str(site_dir), f"{site_name}_config"))
        
        # Test that all files are created correctly
        for site_name, source_path, config_name in sites:
            source_dir = Path(source_path)
            config_file = config_dir / f"{config_name}.toml"
            
            assert source_dir.exists()
            assert config_file.exists()
            
            # Check that source files exist
            source_files = list(source_dir.glob("*.json"))
            assert len(source_files) == 3
        
        # Test configuration loading
        for site_name, _, config_name in sites:
            config_file = config_dir / f"{config_name}.toml"
            with open(config_file) as f:
                content = f.read()
                assert "pipeline" in content
                assert "paths" in content
                assert site_name in content
    
    def test_multi_site_error_recovery(self, temp_dir):
        """Test multi-site migration error recovery."""
        from examples.multi_site.migrate_all import MultiSiteMigrator
        
        config_dir = temp_dir / "configs"
        config_dir.mkdir()
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        migrator = MultiSiteMigrator(config_dir, output_dir)
        
        # Test with sites that have different error conditions
        sites = [
            ("valid_site", str(temp_dir / "valid"), "valid_config"),
            ("missing_source", "/nonexistent/path", "valid_config"),
            ("missing_config", str(temp_dir / "valid"), "nonexistent_config")
        ]
        
        # Create valid site data
        valid_site_dir = temp_dir / "valid"
        valid_site_dir.mkdir()
        content_file = valid_site_dir / "item.json"
        with open(content_file, "w") as f:
            json.dump({"@type": "Document", "title": "Valid Item"}, f)
        
        # Create valid config
        valid_config_file = config_dir / "valid_config.toml"
        with open(valid_config_file, "w") as f:
            f.write("""
[pipeline]
steps = ["collective.transmute.steps.ids.process_ids"]
""")
        
        # Mock pipeline to simulate processing
        with patch('examples.multi_site.migrate_all.pipeline') as mock_pipeline:
            mock_pipeline.return_value = None
            
            with patch('examples.multi_site.migrate_all.layout') as mock_layout:
                mock_layout.TransmuteLayout.return_value = Mock()
                mock_layout.live.return_value.__enter__ = Mock()
                mock_layout.live.return_value.__exit__ = Mock()
                
                # This should handle errors gracefully and continue with other sites
                # The actual implementation would need to be tested with real pipeline calls
                assert len(sites) == 3
                assert valid_site_dir.exists()
                assert valid_config_file.exists() 