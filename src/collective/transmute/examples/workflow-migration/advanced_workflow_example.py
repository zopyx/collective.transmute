#!/usr/bin/env python3
"""
Advanced workflow migration example for collective.transmute.

This example demonstrates complex workflow migration scenarios including:
- Multiple workflow state mappings
- Workflow history cleanup and transformation
- Custom workflow transition handling
- State validation and consistency checks
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from collective.transmute import _types as t
from collective.transmute.settings import pb_config


@dataclass
class WorkflowTransition:
    """Represents a workflow transition."""
    
    name: str
    from_state: str
    to_state: str
    actor: str
    comments: str
    timestamp: str
    workflow_id: str = "plone_workflow"


class AdvancedWorkflowProcessor:
    """Advanced workflow processor for complex migration scenarios."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the workflow processor.
        
        Args:
            config: Configuration dictionary for workflow processing
        """
        self.config = config
        self.state_mapping = config.get("state_mapping", {})
        self.workflow_mapping = config.get("workflow_mapping", {})
        self.transition_rules = config.get("transition_rules", {})
        self.history_cleanup = config.get("history_cleanup", {})
    
    def _map_workflow_state(self, old_state: str, content_type: str) -> str:
        """Map old workflow state to new state based on content type.
        
        Args:
            old_state: Original workflow state
            content_type: Content type for context
            
        Returns:
            Mapped workflow state
        """
        # Check for content type specific mapping
        type_mapping = self.state_mapping.get(content_type, {})
        if old_state in type_mapping:
            return type_mapping[old_state]
        
        # Fall back to global mapping
        return self.state_mapping.get(old_state, old_state)
    
    def _clean_workflow_history(
        self, 
        history: List[Dict[str, Any]], 
        max_entries: int = 50,
        preserve_actors: bool = True
    ) -> List[Dict[str, Any]]:
        """Clean and validate workflow history.
        
        Args:
            history: List of workflow history entries
            max_entries: Maximum number of entries to keep
            preserve_actors: Whether to preserve actor information
            
        Returns:
            Cleaned workflow history
        """
        if not history:
            return []
        
        # Sort by timestamp (newest first)
        sorted_history = sorted(
            history, 
            key=lambda x: x.get("time", x.get("timestamp", "")), 
            reverse=True
        )
        
        # Keep only the most recent entries
        cleaned_history = sorted_history[:max_entries]
        
        # Clean and validate each entry
        for entry in cleaned_history:
            # Ensure required fields
            if "time" not in entry and "timestamp" in entry:
                entry["time"] = entry["timestamp"]
            
            if "time" not in entry:
                entry["time"] = datetime.now().isoformat()
            
            if "actor" not in entry or not preserve_actors:
                entry["actor"] = "system"
            
            if "comments" not in entry:
                entry["comments"] = ""
            
            # Map review states in history
            if "review_state" in entry:
                entry["review_state"] = self._map_workflow_state(
                    entry["review_state"], 
                    entry.get("content_type", "Document")
                )
        
        return cleaned_history
    
    def _validate_workflow_transitions(
        self, 
        transitions: List[Dict[str, Any]], 
        content_type: str
    ) -> List[Dict[str, Any]]:
        """Validate and clean workflow transitions.
        
        Args:
            transitions: List of workflow transitions
            content_type: Content type for validation
            
        Returns:
            Validated transitions
        """
        if not transitions:
            return []
        
        validated_transitions = []
        
        for transition in transitions:
            # Validate required fields
            if not all(key in transition for key in ["name", "to_state"]):
                continue
            
            # Map states
            if "from_state" in transition:
                transition["from_state"] = self._map_workflow_state(
                    transition["from_state"], content_type
                )
            
            transition["to_state"] = self._map_workflow_state(
                transition["to_state"], content_type
            )
            
            # Ensure actor and timestamp
            if "actor" not in transition:
                transition["actor"] = "system"
            
            if "timestamp" not in transition:
                transition["timestamp"] = datetime.now().isoformat()
            
            validated_transitions.append(transition)
        
        return validated_transitions
    
    async def process_advanced_workflow(
        self, 
        item: t.PloneItem, 
        metadata: t.MetadataInfo
    ) -> t.PloneItemGenerator:
        """Process workflow with advanced features.
        
        This processor handles:
        - Content type specific state mapping
        - Workflow history cleanup and validation
        - Custom transition processing
        - State consistency validation
        
        Args:
            item: Plone item to process
            metadata: Metadata information for the transformation
            
        Yields:
            Item with processed workflow information
        """
        
        content_type = item.get("@type", "Document")
        current_state = item.get("review_state", "private")
        
        # Map workflow state
        new_state = self._map_workflow_state(current_state, content_type)
        item["review_state"] = new_state
        
        # Handle workflow history
        if workflow_history := item.get("workflow_history", {}):
            cleaned_history = {}
            
            for workflow_id, history in workflow_history.items():
                if isinstance(history, list):
                    # Clean history entries
                    cleaned_entries = self._clean_workflow_history(
                        history,
                        max_entries=self.history_cleanup.get("max_entries", 50),
                        preserve_actors=self.history_cleanup.get("preserve_actors", True)
                    )
                    
                    # Map states in history
                    for entry in cleaned_entries:
                        if "review_state" in entry:
                            entry["review_state"] = self._map_workflow_state(
                                entry["review_state"], content_type
                            )
                    
                    cleaned_history[workflow_id] = cleaned_entries
            
            item["workflow_history"] = cleaned_history
        
        # Handle custom workflow transitions
        if custom_transitions := item.pop("_custom_transitions", None):
            validated_transitions = self._validate_workflow_transitions(
                custom_transitions, content_type
            )
            
            # Add transitions to workflow history
            if validated_transitions:
                if "workflow_history" not in item:
                    item["workflow_history"] = {}
                
                for workflow_id in item["workflow_history"]:
                    if isinstance(item["workflow_history"][workflow_id], list):
                        for transition in validated_transitions:
                            transition_entry = {
                                "action": transition["name"],
                                "actor": transition["actor"],
                                "comments": transition.get("comments", ""),
                                "review_state": transition["to_state"],
                                "time": transition["timestamp"]
                            }
                            item["workflow_history"][workflow_id].append(transition_entry)
        
        # Set content type specific workflow
        workflow_name = self.workflow_mapping.get(content_type, "simple_publication_workflow")
        item["workflow"] = workflow_name
        
        # Apply transition rules
        if transition_rules := self.transition_rules.get(content_type):
            # Apply any content type specific transition rules
            for rule in transition_rules:
                if self._should_apply_rule(item, rule):
                    item = self._apply_transition_rule(item, rule)
        
        # Validate final state
        item = self._validate_final_state(item, content_type)
        
        yield item
    
    def _should_apply_rule(self, item: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Check if a transition rule should be applied.
        
        Args:
            item: Item to check
            rule: Rule to evaluate
            
        Returns:
            True if rule should be applied
        """
        conditions = rule.get("conditions", {})
        
        for field, expected_value in conditions.items():
            if item.get(field) != expected_value:
                return False
        
        return True
    
    def _apply_transition_rule(self, item: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a transition rule to an item.
        
        Args:
            item: Item to modify
            rule: Rule to apply
            
        Returns:
            Modified item
        """
        actions = rule.get("actions", {})
        
        for field, value in actions.items():
            if field == "review_state":
                item["review_state"] = value
            elif field == "workflow":
                item["workflow"] = value
            else:
                item[field] = value
        
        return item
    
    def _validate_final_state(self, item: Dict[str, Any], content_type: str) -> Dict[str, Any]:
        """Validate the final workflow state.
        
        Args:
            item: Item to validate
            content_type: Content type for validation
            
        Returns:
            Validated item
        """
        # Ensure required fields are present
        if not item.get("review_state"):
            default_state = self.state_mapping.get(content_type, {}).get("default", "private")
            item["review_state"] = default_state
        
        # Validate workflow history structure
        if workflow_history := item.get("workflow_history", {}):
            for workflow_id, history in workflow_history.items():
                if not isinstance(history, list):
                    item["workflow_history"][workflow_id] = []
        
        # Ensure workflow field is set
        if not item.get("workflow"):
            workflow_name = self.workflow_mapping.get(content_type, "simple_publication_workflow")
            item["workflow"] = workflow_name
        
        return item


# Example configuration for advanced workflow processing
ADVANCED_WORKFLOW_CONFIG = {
    "state_mapping": {
        # Global state mappings
        "private": "private",
        "published": "published",
        "pending": "pending_review",
        "draft": "draft",
        "archived": "archived",
        "rejected": "rejected",
        
        # Content type specific mappings
        "Document": {
            "private": "private",
            "published": "published",
            "pending": "pending_review",
            "draft": "draft"
        },
        "News Item": {
            "private": "private",
            "published": "published",
            "pending": "pending_review",
            "draft": "draft",
            "archived": "archived"
        },
        "Event": {
            "private": "private",
            "published": "published",
            "pending": "pending_review",
            "draft": "draft",
            "expired": "expired"
        }
    },
    
    "workflow_mapping": {
        "Document": "simple_publication_workflow",
        "News Item": "news_workflow",
        "Event": "event_workflow",
        "Folder": "simple_publication_workflow"
    },
    
    "transition_rules": {
        "Event": [
            {
                "conditions": {"review_state": "published"},
                "actions": {"effective": "now"}
            },
            {
                "conditions": {"review_state": "expired"},
                "actions": {"expires": "past"}
            }
        ]
    },
    
    "history_cleanup": {
        "max_entries": 50,
        "preserve_actors": True,
        "remove_duplicates": True
    }
}


async def process_advanced_workflow(
    item: t.PloneItem, 
    metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Main workflow processing function.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Item with processed workflow information
    """
    
    processor = AdvancedWorkflowProcessor(ADVANCED_WORKFLOW_CONFIG)
    
    async for processed_item in processor.process_advanced_workflow(item, metadata):
        yield processed_item


# Example usage
async def example_usage():
    """Example usage of the advanced workflow processor."""
    
    # Example item with complex workflow history
    example_item = {
        "@type": "News Item",
        "@id": "/Plone/news/example-news",
        "UID": "example-uid-123",
        "title": "Example News Item",
        "review_state": "pending",
        "workflow_history": {
            "news_workflow": [
                {
                    "action": "create",
                    "actor": "admin",
                    "comments": "Item created",
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
        "_custom_transitions": [
            {
                "name": "publish",
                "from_state": "pending",
                "to_state": "published",
                "actor": "reviewer",
                "comments": "Approved for publication",
                "timestamp": "2023-01-03T09:15:00Z"
            }
        ]
    }
    
    # Process the item
    metadata = t.MetadataInfo(path=Path("example"))
    
    print("Original item:")
    print(json.dumps(example_item, indent=2))
    print("\n" + "="*50 + "\n")
    
    async for processed_item in process_advanced_workflow(example_item, metadata):
        print("Processed item:")
        print(json.dumps(processed_item, indent=2))


if __name__ == "__main__":
    asyncio.run(example_usage()) 