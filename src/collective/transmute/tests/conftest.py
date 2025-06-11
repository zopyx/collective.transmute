"""
Pytest configuration and common fixtures for collective.transmute examples tests.
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from collective.transmute import _types as t


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_plone_item():
    """Create a sample Plone item for testing."""
    return {
        "@type": "Document",
        "@id": "/Plone/test-document",
        "UID": "test-uid-123",
        "title": "Test Document",
        "description": "A test document for migration",
        "text": {"data": "<p>Test content</p>", "content-type": "text/html"},
        "review_state": "private",
        "created": "2023-01-01T10:00:00Z",
        "modified": "2023-01-02T15:30:00Z",
        "creators": ["admin"],
        "subjects": ["test", "migration"]
    }


@pytest.fixture
def sample_news_item():
    """Create a sample News Item for testing."""
    return {
        "@type": "News Item",
        "@id": "/Plone/news/test-news",
        "UID": "news-uid-456",
        "title": "Test News Item",
        "description": "A test news item",
        "text": {"data": "<p>News content</p>", "content-type": "text/html"},
        "review_state": "published",
        "effective": "2023-01-01T12:00:00Z",
        "expires": "2023-12-31T23:59:59Z",
        "creators": ["editor"],
        "subjects": ["news", "test"]
    }


@pytest.fixture
def sample_event_item():
    """Create a sample Event for testing."""
    return {
        "@type": "Event",
        "@id": "/Plone/events/test-event",
        "UID": "event-uid-789",
        "title": "Test Event",
        "description": "A test event",
        "text": {"data": "<p>Event details</p>", "content-type": "text/html"},
        "start": "2023-02-01T10:00:00Z",
        "end": "2023-02-01T12:00:00Z",
        "location": "Test Location",
        "review_state": "published",
        "creators": ["event_manager"],
        "subjects": ["event", "test"]
    }


@pytest.fixture
def sample_custom_news_item():
    """Create a sample custom news item for testing."""
    return {
        "@type": "CustomNewsItem",
        "@id": "/Plone/custom-news/test",
        "UID": "custom-news-uid-123",
        "custom_title": "Custom News Title",
        "custom_body": "<p>Custom news body content</p>",
        "custom_image": {"data": "image-data", "content-type": "image/jpeg"},
        "custom_date": "2023-01-15T10:00:00Z",
        "custom_author": "custom_author",
        "custom_tags": ["custom", "news", "test"],
        "review_state": "draft"
    }


@pytest.fixture
def sample_workflow_item():
    """Create a sample item with workflow history for testing."""
    return {
        "@type": "Document",
        "@id": "/Plone/workflow-test",
        "UID": "workflow-uid-123",
        "title": "Workflow Test Document",
        "review_state": "pending",
        "workflow_history": {
            "simple_publication_workflow": [
                {
                    "action": "create",
                    "actor": "admin",
                    "comments": "Document created",
                    "review_state": "private",
                    "time": "2023-01-01T10:00:00Z"
                },
                {
                    "action": "submit",
                    "actor": "editor",
                    "comments": "Ready for review",
                    "review_state": "pending",
                    "time": "2023-01-02T14:30:00Z"
                }
            ]
        },
        "_workflow_transitions": [
            {
                "name": "publish",
                "actor": "reviewer",
                "comments": "Approved for publication",
                "time": "2023-01-03T09:15:00Z"
            }
        ]
    }


@pytest.fixture
def sample_metadata_info():
    """Create a sample MetadataInfo for testing."""
    return t.MetadataInfo(path=Path("/test/path"))


@pytest.fixture
def mock_console():
    """Create a mock console for testing."""
    console = Mock()
    console.print = Mock()
    console.log = Mock()
    return console


@pytest.fixture
def sample_source_files(sample_plone_item, temp_dir):
    """Create sample source files for testing."""
    # Create a sample JSON file
    sample_file = temp_dir / "test-item.json"
    with open(sample_file, "w") as f:
        json.dump(sample_plone_item, f)
    
    # Create metadata file
    metadata_file = temp_dir / "metadata.json"
    metadata = {
        "export_date": "2023-01-01T10:00:00Z",
        "version": "1.0.0",
        "source": "collective.exportimport"
    }
    with open(metadata_file, "w") as f:
        json.dump(metadata, f)
    
    return t.SourceFiles(
        metadata=metadata,
        content=[sample_file]
    )


@pytest.fixture
def workflow_config():
    """Create a sample workflow configuration for testing."""
    return {
        "state_mapping": {
            "private": "private",
            "published": "published",
            "pending": "pending_review",
            "draft": "draft",
            "archived": "archived"
        },
        "workflow_mapping": {
            "Document": "simple_publication_workflow",
            "News Item": "news_workflow",
            "Event": "event_workflow"
        },
        "history_cleanup": {
            "max_entries": 50,
            "preserve_actors": True
        }
    }


@pytest.fixture
def content_type_config():
    """Create a sample content type configuration for testing."""
    return {
        "field_mapping": {
            "custom_title": "title",
            "custom_body": "text",
            "custom_image": "image",
            "custom_date": "effective",
            "custom_author": "creators",
            "custom_tags": "subjects"
        },
        "portal_type_mapping": {
            "CustomNewsItem": "News Item",
            "CustomEvent": "Event",
            "LegacyDocument": "Document"
        }
    }


@pytest.fixture
def mock_pipeline_state():
    """Create a mock pipeline state for testing."""
    return t.PipelineState(
        total=10,
        processed=0,
        exported=t.defaultdict(int),
        dropped=t.defaultdict(int),
        progress=Mock()
    )


@pytest.fixture
def sample_migration_results():
    """Create sample migration results for testing."""
    return {
        "migration_start": "2023-01-01T10:00:00Z",
        "migration_end": "2023-01-01T11:00:00Z",
        "total_sites": 3,
        "sites": {
            "site1": {
                "status": "success",
                "processed": 100,
                "exported": 95,
                "dropped": 5
            },
            "site2": {
                "status": "success",
                "processed": 50,
                "exported": 48,
                "dropped": 2
            },
            "site3": {
                "status": "error",
                "error": "Configuration error",
                "processed": 0,
                "exported": 0,
                "dropped": 0
            }
        }
    } 