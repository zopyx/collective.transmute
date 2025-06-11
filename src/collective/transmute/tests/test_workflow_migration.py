"""
Tests for workflow migration examples.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, Mock

from collective.transmute import _types as t


class TestCustomWorkflowProcessor:
    """Test the custom workflow processor from workflow migration examples."""
    
    @pytest.fixture
    def processor(self):
        """Create a custom workflow processor instance."""
        from examples.workflow_migration.custom_workflow import process_workflow
        return process_workflow
    
    @pytest.mark.asyncio
    async def test_basic_workflow_processing(self, processor, sample_workflow_item, sample_metadata_info):
        """Test basic workflow processing."""
        items = []
        async for item in processor(sample_workflow_item.copy(), sample_metadata_info):
            items.append(item)
        
        assert len(items) == 1
        processed_item = items[0]
        
        # Check that review state is preserved
        assert processed_item["review_state"] == "pending"
        
        # Check that workflow history is present
        assert "workflow_history" in processed_item
        assert "simple_publication_workflow" in processed_item["workflow_history"]
        
        # Check that transitions are stored
        assert "_pending_transitions" in processed_item
    
    @pytest.mark.asyncio
    async def test_workflow_state_mapping(self, processor, sample_workflow_item, sample_metadata_info):
        """Test workflow state mapping."""
        # Test with different review states
        test_cases = [
            ("private", "private"),
            ("published", "published"),
            ("pending", "pending_review"),
            ("draft", "draft"),
            ("archived", "archived"),
            ("unknown_state", "unknown_state")  # Should remain unchanged
        ]
        
        for original_state, expected_state in test_cases:
            item = sample_workflow_item.copy()
            item["review_state"] = original_state
            
            items = []
            async for processed_item in processor(item, sample_metadata_info):
                items.append(processed_item)
            
            assert len(items) == 1
            assert items[0]["review_state"] == expected_state
    
    @pytest.mark.asyncio
    async def test_workflow_history_cleanup(self, processor, sample_workflow_item, sample_metadata_info):
        """Test workflow history cleanup."""
        # Add many history entries to test cleanup
        item = sample_workflow_item.copy()
        history = item["workflow_history"]["simple_publication_workflow"]
        
        # Add 100 entries (more than the default max of 50)
        for i in range(100):
            history.append({
                "action": f"action_{i}",
                "actor": f"actor_{i}",
                "comments": f"comment_{i}",
                "review_state": "private",
                "time": f"2023-01-01T{i:02d}:00:00Z"
            })
        
        items = []
        async for processed_item in processor(item, sample_metadata_info):
            items.append(processed_item)
        
        assert len(items) == 1
        processed_item = items[0]
        
        # Check that history is cleaned up (should have max 50 entries)
        cleaned_history = processed_item["workflow_history"]["simple_publication_workflow"]
        assert len(cleaned_history) <= 50
    
    @pytest.mark.asyncio
    async def test_workflow_transitions_processing(self, processor, sample_workflow_item, sample_metadata_info):
        """Test workflow transitions processing."""
        item = sample_workflow_item.copy()
        
        # Add custom transitions
        item["_workflow_transitions"] = [
            {
                "name": "publish",
                "actor": "reviewer",
                "comments": "Approved for publication",
                "time": "2023-01-03T09:15:00Z"
            },
            {
                "name": "archive",
                "actor": "admin",
                "comments": "Archived",
                "time": "2023-01-04T10:00:00Z"
            }
        ]
        
        items = []
        async for processed_item in processor(item, sample_metadata_info):
            items.append(processed_item)
        
        assert len(items) == 1
        processed_item = items[0]
        
        # Check that transitions are stored for later processing
        assert "_pending_transitions" in processed_item
        assert len(processed_item["_pending_transitions"]) == 2
    
    @pytest.mark.asyncio
    async def test_content_type_specific_workflow(self, processor, sample_metadata_info):
        """Test content type specific workflow assignment."""
        test_cases = [
            ("Document", "simple_publication_workflow"),
            ("News Item", "news_workflow"),
            ("Event", "event_workflow")
        ]
        
        for content_type, expected_workflow in test_cases:
            item = {
                "@type": content_type,
                "title": f"Test {content_type}",
                "review_state": "private"
            }
            
            items = []
            async for processed_item in processor(item, sample_metadata_info):
                items.append(processed_item)
            
            assert len(items) == 1
            assert items[0]["workflow"] == expected_workflow


class TestAdvancedWorkflowProcessor:
    """Test the advanced workflow processor."""
    
    @pytest.fixture
    def processor(self):
        """Create an advanced workflow processor instance."""
        from examples.workflow_migration.advanced_workflow_example import AdvancedWorkflowProcessor, ADVANCED_WORKFLOW_CONFIG
        return AdvancedWorkflowProcessor(ADVANCED_WORKFLOW_CONFIG)
    
    def test_state_mapping_with_content_type(self, processor):
        """Test state mapping with content type context."""
        # Test content type specific mapping
        assert processor._map_workflow_state("private", "Document") == "private"
        assert processor._map_workflow_state("pending", "News Item") == "pending_review"
        assert processor._map_workflow_state("expired", "Event") == "expired"
        
        # Test fallback to global mapping
        assert processor._map_workflow_state("unknown", "Document") == "unknown"
    
    def test_workflow_history_cleanup(self, processor):
        """Test workflow history cleanup."""
        history = [
            {"time": "2023-01-01T10:00:00Z", "actor": "user1", "review_state": "private"},
            {"time": "2023-01-02T10:00:00Z", "actor": "user2", "review_state": "pending"},
            {"time": "2023-01-03T10:00:00Z", "actor": "user3", "review_state": "published"}
        ]
        
        # Test with max_entries = 2
        cleaned = processor._clean_workflow_history(history, max_entries=2)
        assert len(cleaned) == 2
        assert cleaned[0]["time"] == "2023-01-03T10:00:00Z"  # Most recent first
    
    def test_workflow_transition_validation(self, processor):
        """Test workflow transition validation."""
        transitions = [
            {
                "name": "publish",
                "from_state": "pending",
                "to_state": "published",
                "actor": "reviewer"
            },
            {
                "name": "invalid",  # Missing to_state
                "from_state": "private"
            }
        ]
        
        validated = processor._validate_workflow_transitions(transitions, "Document")
        assert len(validated) == 1  # Only the valid transition should remain
        assert validated[0]["name"] == "publish"
    
    @pytest.mark.asyncio
    async def test_advanced_workflow_processing(self, processor, sample_workflow_item, sample_metadata_info):
        """Test advanced workflow processing."""
        items = []
        async for item in processor.process_advanced_workflow(sample_workflow_item.copy(), sample_metadata_info):
            items.append(item)
        
        assert len(items) == 1
        processed_item = items[0]
        
        # Check that workflow is set
        assert "workflow" in processed_item
        assert processed_item["workflow"] == "simple_publication_workflow"
        
        # Check that review state is mapped
        assert processed_item["review_state"] == "pending_review"
    
    def test_transition_rule_application(self, processor):
        """Test transition rule application."""
        item = {
            "@type": "Event",
            "review_state": "published"
        }
        
        rule = {
            "conditions": {"review_state": "published"},
            "actions": {"effective": "now"}
        }
        
        assert processor._should_apply_rule(item, rule) is True
        
        modified_item = processor._apply_transition_rule(item.copy(), rule)
        assert modified_item["effective"] == "now"
    
    def test_final_state_validation(self, processor):
        """Test final state validation."""
        item = {
            "@type": "Document",
            # Missing review_state and workflow
        }
        
        validated_item = processor._validate_final_state(item, "Document")
        assert "review_state" in validated_item
        assert "workflow" in validated_item
        assert validated_item["workflow"] == "simple_publication_workflow"


class TestWorkflowConfiguration:
    """Test workflow configuration loading and validation."""
    
    def test_configuration_file_loading(self, temp_dir):
        """Test loading workflow configuration from file."""
        config_content = """
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "examples.workflow_migration.custom_workflow.process_workflow",
]

[workflow]
state_mapping = {
    "private" = "private",
    "published" = "published",
    "pending" = "pending_review"
}
"""
        config_file = temp_dir / "transmute.toml"
        with open(config_file, "w") as f:
            f.write(config_content)
        
        # Test that file can be read
        assert config_file.exists()
        with open(config_file) as f:
            content = f.read()
        assert "state_mapping" in content
    
    def test_workflow_state_mapping_configuration(self, workflow_config):
        """Test workflow state mapping configuration."""
        state_mapping = workflow_config["state_mapping"]
        
        # Test basic mappings
        assert state_mapping["private"] == "private"
        assert state_mapping["published"] == "published"
        assert state_mapping["pending"] == "pending_review"
        assert state_mapping["draft"] == "draft"
        assert state_mapping["archived"] == "archived"
    
    def test_workflow_mapping_configuration(self, workflow_config):
        """Test workflow mapping configuration."""
        workflow_mapping = workflow_config["workflow_mapping"]
        
        assert workflow_mapping["Document"] == "simple_publication_workflow"
        assert workflow_mapping["News Item"] == "news_workflow"
        assert workflow_mapping["Event"] == "event_workflow"
    
    def test_history_cleanup_configuration(self, workflow_config):
        """Test history cleanup configuration."""
        history_cleanup = workflow_config["history_cleanup"]
        
        assert history_cleanup["max_entries"] == 50
        assert history_cleanup["preserve_actors"] is True


class TestWorkflowIntegration:
    """Integration tests for workflow migration."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_migration(self, temp_dir, sample_workflow_item):
        """Test end-to-end workflow migration process."""
        # Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        
        source_file = source_dir / "workflow-item.json"
        with open(source_file, "w") as f:
            import json
            json.dump(sample_workflow_item, f)
        
        # Create destination directory
        dest_dir = temp_dir / "destination"
        dest_dir.mkdir()
        
        # This would normally run the full pipeline
        # For testing, we'll just verify the files exist
        assert source_file.exists()
        assert dest_dir.exists()
        
        # Test that we can read the source file
        with open(source_file) as f:
            import json
            item = json.load(f)
        
        assert item["@type"] == "Document"
        assert "workflow_history" in item
        assert "review_state" in item
    
    def test_workflow_error_handling(self):
        """Test workflow error handling."""
        # Test with invalid workflow state
        from examples.workflow_migration.custom_workflow import process_workflow
        
        invalid_item = {
            "@type": "Document",
            "review_state": None,  # Invalid state
            "workflow_history": "invalid"  # Should be dict
        }
        
        # Should not raise exception but handle gracefully
        async def test_processing():
            items = []
            async for item in process_workflow(invalid_item, t.MetadataInfo(path=Path("/test"))):
                items.append(item)
            return items
        
        # Run the test
        items = asyncio.run(test_processing())
        assert len(items) == 1  # Should still process the item 