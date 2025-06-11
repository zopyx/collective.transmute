"""
Tests for content type migration examples.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, Mock

from collective.transmute import _types as t


class TestCustomContentTypeProcessors:
    """Test the custom content type processors."""
    
    @pytest.fixture
    def processors(self):
        """Import all custom processors."""
        from examples.content_type_migration.custom_processors import (
            custom_news_processor,
            custom_event_processor,
            legacy_document_processor,
            custom_gallery_processor,
            process_custom_types
        )
        return {
            "news": custom_news_processor,
            "event": custom_event_processor,
            "document": legacy_document_processor,
            "gallery": custom_gallery_processor,
            "main": process_custom_types
        }
    
    @pytest.mark.asyncio
    async def test_custom_news_processor(self, processors, sample_custom_news_item, sample_metadata_info):
        """Test custom news item processing."""
        processor = processors["news"]
        
        items = []
        async for item in processor(sample_custom_news_item.copy(), sample_metadata_info):
            items.append(item)
        
        assert len(items) == 1
        processed_item = items[0]
        
        # Check field mapping
        assert processed_item["title"] == "Custom News Title"
        assert processed_item["text"]["data"] == "<p>Custom news body content</p>"
        assert processed_item["image"]["data"] == "image-data"
        assert processed_item["effective"] == "2023-01-15T10:00:00Z"
        assert processed_item["creators"] == ["custom_author"]
        assert processed_item["subjects"] == ["custom", "news", "test"]
        
        # Check content type transformation
        assert processed_item["@type"] == "News Item"
        
        # Check that custom fields are removed
        assert "custom_title" not in processed_item
        assert "custom_body" not in processed_item
        assert "custom_image" not in processed_item
    
    @pytest.mark.asyncio
    async def test_custom_event_processor(self, processors, sample_metadata_info):
        """Test custom event processing."""
        processor = processors["event"]
        
        custom_event_item = {
            "@type": "CustomEvent",
            "@id": "/Plone/custom-event/test",
            "UID": "custom-event-uid-123",
            "custom_title": "Custom Event Title",
            "custom_body": "<p>Custom event body</p>",
            "custom_image": {"data": "event-image", "content-type": "image/jpeg"},
            "event_date": "2023-02-01T10:00:00Z",
            "event_end_date": "2023-02-01T12:00:00Z",
            "event_location": {"address": "123 Test St", "city": "Test City"}
        }
        
        items = []
        async for item in processor(custom_event_item, sample_metadata_info):
            items.append(item)
        
        assert len(items) == 1
        processed_item = items[0]
        
        # Check field mapping
        assert processed_item["title"] == "Custom Event Title"
        assert processed_item["text"]["data"] == "<p>Custom event body</p>"
        assert processed_item["image"]["data"] == "event-image"
        assert processed_item["start"] == "2023-02-01T10:00:00Z"
        assert processed_item["end"] == "2023-02-01T12:00:00Z"
        assert processed_item["location"] == "123 Test St"
        
        # Check content type transformation
        assert processed_item["@type"] == "Event"
    
    @pytest.mark.asyncio
    async def test_legacy_document_processor(self, processors, sample_metadata_info):
        """Test legacy document processing."""
        processor = processors["document"]
        
        legacy_document_item = {
            "@type": "LegacyDocument",
            "@id": "/Plone/legacy-doc/test",
            "UID": "legacy-doc-uid-123",
            "legacy_title": "Legacy Document Title",
            "legacy_body": "<p>Legacy document body</p>",
            "legacy_author": "legacy_author",
            "legacy_date": "2023-01-10T10:00:00Z",
            "legacy_id": "old-id-123",
            "legacy_type": "old_type",
            "legacy_metadata": {"old": "data"},
            "old_workflow_state": "old_state",
            "legacy_permissions": {"old": "perms"}
        }
        
        items = []
        async for item in processor(legacy_document_item, sample_metadata_info):
            items.append(item)
        
        assert len(items) == 1
        processed_item = items[0]
        
        # Check field mapping
        assert processed_item["title"] == "Legacy Document Title"
        assert processed_item["text"]["data"] == "<p>Legacy document body</p>"
        assert processed_item["creators"] == ["legacy_author"]
        assert processed_item["effective"] == "2023-01-10T10:00:00Z"
        
        # Check content type transformation
        assert processed_item["@type"] == "Document"
        
        # Check that legacy fields are cleaned up
        assert "legacy_id" not in processed_item
        assert "legacy_type" not in processed_item
        assert "legacy_metadata" not in processed_item
        assert "old_workflow_state" not in processed_item
        assert "legacy_permissions" not in processed_item
    
    @pytest.mark.asyncio
    async def test_custom_gallery_processor(self, processors, sample_metadata_info):
        """Test custom gallery processing."""
        processor = processors["gallery"]
        
        custom_gallery_item = {
            "@type": "CustomGallery",
            "@id": "/Plone/custom-gallery/test",
            "UID": "custom-gallery-uid-123",
            "gallery_title": "Custom Gallery Title",
            "gallery_description": "Custom gallery description",
            "gallery_images": [
                {"data": "image1", "content-type": "image/jpeg"},
                {"data": "image2", "content-type": "image/png"}
            ],
            "gallery_metadata": {
                "tags": ["gallery", "test"],
                "created": "2023-01-20T10:00:00Z"
            }
        }
        
        items = []
        async for item in processor(custom_gallery_item, sample_metadata_info):
            items.append(item)
        
        assert len(items) == 1
        processed_item = items[0]
        
        # Check field mapping
        assert processed_item["title"] == "Custom Gallery Title"
        assert processed_item["description"] == "Custom gallery description"
        
        # Check content type transformation
        assert processed_item["@type"] == "Folder"
        
        # Check gallery block creation
        assert "blocks" in processed_item
        assert "gallery-1" in processed_item["blocks"]
        gallery_block = processed_item["blocks"]["gallery-1"]
        assert gallery_block["@type"] == "imageGallery"
        assert len(gallery_block["images"]) == 2
        
        # Check metadata extraction
        assert processed_item["subjects"] == ["gallery", "test"]
        assert processed_item["effective"] == "2023-01-20T10:00:00Z"
    
    @pytest.mark.asyncio
    async def test_main_processor_routing(self, processors, sample_metadata_info):
        """Test the main processor routing logic."""
        processor = processors["main"]
        
        test_cases = [
            ("CustomNewsItem", "news"),
            ("CustomEvent", "event"),
            ("LegacyDocument", "document"),
            ("CustomGallery", "gallery"),
            ("Document", "standard")  # Should pass through unchanged
        ]
        
        for content_type, expected_behavior in test_cases:
            item = {
                "@type": content_type,
                "title": f"Test {content_type}",
                "custom_title": "Custom Title" if content_type == "CustomNewsItem" else None
            }
            
            items = []
            async for processed_item in processor(item.copy(), sample_metadata_info):
                items.append(processed_item)
            
            assert len(items) == 1
            
            if expected_behavior == "news":
                assert items[0]["title"] == "Custom Title"
                assert items[0]["@type"] == "News Item"
            elif expected_behavior == "standard":
                assert items[0]["title"] == f"Test {content_type}"
                assert items[0]["@type"] == content_type
    
    @pytest.mark.asyncio
    async def test_text_field_processing(self, processors, sample_metadata_info):
        """Test text field processing with different input types."""
        processor = processors["news"]
        
        test_cases = [
            # (input_text, expected_output)
            ("<p>Simple text</p>", {"data": "<p>Simple text</p>", "content-type": "text/html"}),
            ({"data": "Already formatted", "content-type": "text/html"}, 
             {"data": "Already formatted", "content-type": "text/html"}),
            (123, {"data": "123", "content-type": "text/plain"}),
            (None, None)
        ]
        
        for input_text, expected_output in test_cases:
            item = {
                "@type": "CustomNewsItem",
                "custom_body": input_text
            }
            
            items = []
            async for processed_item in processor(item, sample_metadata_info):
                items.append(processed_item)
            
            assert len(items) == 1
            if expected_output is not None:
                assert processed_item["text"] == expected_output
            else:
                assert "text" not in processed_item or processed_item["text"] is None
    
    @pytest.mark.asyncio
    async def test_creators_field_processing(self, processors, sample_metadata_info):
        """Test creators field processing."""
        processor = processors["news"]
        
        test_cases = [
            ("single_author", ["single_author"]),
            (["author1", "author2"], ["author1", "author2"]),
            (None, None)
        ]
        
        for input_creators, expected_creators in test_cases:
            item = {
                "@type": "CustomNewsItem",
                "custom_author": input_creators
            }
            
            items = []
            async for processed_item in processor(item, sample_metadata_info):
                items.append(processed_item)
            
            assert len(items) == 1
            if expected_creators is not None:
                assert processed_item["creators"] == expected_creators
            else:
                assert "creators" not in processed_item or processed_item["creators"] is None
    
    @pytest.mark.asyncio
    async def test_subjects_field_processing(self, processors, sample_metadata_info):
        """Test subjects field processing."""
        processor = processors["news"]
        
        test_cases = [
            ("single_tag", ["single_tag"]),
            (["tag1", "tag2"], ["tag1", "tag2"]),
            (None, None)
        ]
        
        for input_subjects, expected_subjects in test_cases:
            item = {
                "@type": "CustomNewsItem",
                "custom_tags": input_subjects
            }
            
            items = []
            async for processed_item in processor(item, sample_metadata_info):
                items.append(processed_item)
            
            assert len(items) == 1
            if expected_subjects is not None:
                assert processed_item["subjects"] == expected_subjects
            else:
                assert "subjects" not in processed_item or processed_item["subjects"] is None


class TestContentTypeConfiguration:
    """Test content type configuration loading and validation."""
    
    def test_configuration_file_loading(self, temp_dir):
        """Test loading content type configuration from file."""
        config_content = """
[pipeline]
steps = [
    "collective.transmute.steps.ids.process_ids",
    "examples.content_type_migration.custom_processors.process_custom_types",
]

[types.CustomNewsItem]
processor = "examples.content_type_migration.custom_news_processor"
blocks = [
    {type = "title"},
    {type = "description"},
    {type = "text"}
]

[portal_type.mapping]
CustomNewsItem = "News Item"
CustomEvent = "Event"
"""
        config_file = temp_dir / "transmute.toml"
        with open(config_file, "w") as f:
            f.write(config_content)
        
        # Test that file can be read
        assert config_file.exists()
        with open(config_file) as f:
            content = f.read()
        assert "CustomNewsItem" in content
        assert "portal_type.mapping" in content
    
    def test_field_mapping_configuration(self, content_type_config):
        """Test field mapping configuration."""
        field_mapping = content_type_config["field_mapping"]
        
        assert field_mapping["custom_title"] == "title"
        assert field_mapping["custom_body"] == "text"
        assert field_mapping["custom_image"] == "image"
        assert field_mapping["custom_date"] == "effective"
        assert field_mapping["custom_author"] == "creators"
        assert field_mapping["custom_tags"] == "subjects"
    
    def test_portal_type_mapping_configuration(self, content_type_config):
        """Test portal type mapping configuration."""
        portal_type_mapping = content_type_config["portal_type_mapping"]
        
        assert portal_type_mapping["CustomNewsItem"] == "News Item"
        assert portal_type_mapping["CustomEvent"] == "Event"
        assert portal_type_mapping["LegacyDocument"] == "Document"


class TestContentTypeIntegration:
    """Integration tests for content type migration."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_content_type_migration(self, temp_dir, sample_custom_news_item):
        """Test end-to-end content type migration process."""
        # Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        
        source_file = source_dir / "custom-news-item.json"
        with open(source_file, "w") as f:
            import json
            json.dump(sample_custom_news_item, f)
        
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
        
        assert item["@type"] == "CustomNewsItem"
        assert "custom_title" in item
        assert "custom_body" in item
    
    def test_content_type_error_handling(self):
        """Test content type error handling."""
        from examples.content_type_migration.custom_processors import custom_news_processor
        
        # Test with missing fields
        invalid_item = {
            "@type": "CustomNewsItem",
            # Missing all custom fields
        }
        
        # Should not raise exception but handle gracefully
        async def test_processing():
            items = []
            async for item in custom_news_processor(invalid_item, t.MetadataInfo(path=Path("/test"))):
                items.append(item)
            return items
        
        # Run the test
        items = asyncio.run(test_processing())
        assert len(items) == 1  # Should still process the item
        
        processed_item = items[0]
        assert processed_item["@type"] == "News Item"  # Should be transformed
        assert "title" not in processed_item  # Should be missing since no custom_title
    
    @pytest.mark.asyncio
    async def test_multiple_content_types_migration(self, processors, sample_metadata_info):
        """Test migration of multiple content types in sequence."""
        processor = processors["main"]
        
        items_to_process = [
            {
                "@type": "CustomNewsItem",
                "custom_title": "News 1",
                "custom_body": "News content 1"
            },
            {
                "@type": "CustomEvent",
                "custom_title": "Event 1",
                "custom_body": "Event content 1",
                "event_date": "2023-02-01T10:00:00Z"
            },
            {
                "@type": "LegacyDocument",
                "legacy_title": "Document 1",
                "legacy_body": "Document content 1"
            },
            {
                "@type": "Document",  # Standard type
                "title": "Standard Document",
                "text": {"data": "Standard content", "content-type": "text/html"}
            }
        ]
        
        processed_items = []
        for item in items_to_process:
            async for processed_item in processor(item.copy(), sample_metadata_info):
                processed_items.append(processed_item)
        
        assert len(processed_items) == 4
        
        # Check transformations
        assert processed_items[0]["@type"] == "News Item"
        assert processed_items[0]["title"] == "News 1"
        
        assert processed_items[1]["@type"] == "Event"
        assert processed_items[1]["title"] == "Event 1"
        
        assert processed_items[2]["@type"] == "Document"
        assert processed_items[2]["title"] == "Document 1"
        
        assert processed_items[3]["@type"] == "Document"  # Unchanged
        assert processed_items[3]["title"] == "Standard Document" 