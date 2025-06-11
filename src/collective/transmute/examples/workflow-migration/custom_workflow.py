"""
Custom workflow processing step for collective.transmute.

This module provides advanced workflow state migration functionality,
including state mapping, history cleanup, and workflow transition handling.
"""

from collective.transmute import _types as t
from collective.transmute.settings import pb_config
from datetime import datetime
from typing import Dict, List, Any


def _clean_workflow_history(history: List[Dict[str, Any]], max_entries: int = 50) -> List[Dict[str, Any]]:
    """Clean and limit workflow history entries.
    
    Args:
        history: List of workflow history entries
        max_entries: Maximum number of entries to keep
        
    Returns:
        Cleaned workflow history
    """
    if not history:
        return []
    
    # Sort by time (newest first)
    sorted_history = sorted(history, key=lambda x: x.get("time", ""), reverse=True)
    
    # Keep only the most recent entries
    cleaned_history = sorted_history[:max_entries]
    
    # Ensure required fields are present
    for entry in cleaned_history:
        if "time" not in entry:
            entry["time"] = datetime.now().isoformat()
        if "actor" not in entry:
            entry["actor"] = "system"
        if "comments" not in entry:
            entry["comments"] = ""
    
    return cleaned_history


def _map_workflow_state(old_state: str, state_mapping: Dict[str, str]) -> str:
    """Map old workflow state to new state.
    
    Args:
        old_state: Original workflow state
        state_mapping: Mapping from old to new states
        
    Returns:
        Mapped workflow state
    """
    return state_mapping.get(old_state, old_state)


async def process_workflow(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process workflow states and transitions.
    
    This step handles:
    - Workflow state mapping from old to new states
    - Workflow history cleanup and validation
    - Setting appropriate default states for content types
    - Handling workflow transitions and comments
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Item with processed workflow information
    """
    
    # Get configuration
    workflow_config = pb_config.get("workflow", {})
    state_mapping = workflow_config.get("state_mapping", {})
    history_config = workflow_config.get("history", {})
    max_entries = history_config.get("max_entries", 50)
    
    # Get current review state
    current_state = item.get("review_state", "private")
    
    # Map to new state
    new_state = _map_workflow_state(current_state, state_mapping)
    item["review_state"] = new_state
    
    # Handle workflow history
    if workflow_history := item.get("workflow_history", {}):
        cleaned_history = {}
        
        for workflow_id, history in workflow_history.items():
            if isinstance(history, list):
                # Clean and limit history entries
                cleaned_entries = _clean_workflow_history(history, max_entries)
                
                # Map states in history entries
                for entry in cleaned_entries:
                    if "review_state" in entry:
                        entry["review_state"] = _map_workflow_state(
                            entry["review_state"], state_mapping
                        )
                
                cleaned_history[workflow_id] = cleaned_entries
        
        item["workflow_history"] = cleaned_history
    
    # Set content type specific workflow
    content_type = item.get("@type", "Document")
    type_config = pb_config.types.get(content_type, {})
    
    if workflow_name := type_config.get("workflow"):
        item["workflow"] = workflow_name
    
    # Set default state if not present
    if not item.get("review_state"):
        default_state = type_config.get("default_state", "private")
        item["review_state"] = default_state
    
    # Handle workflow transitions
    if transitions := item.pop("_workflow_transitions", None):
        # Store transitions for later processing
        item["_pending_transitions"] = transitions
    
    # Handle workflow comments
    if workflow_comments := item.pop("_workflow_comments", None):
        # Add comments to workflow history
        if "workflow_history" not in item:
            item["workflow_history"] = {}
        
        for workflow_id, history in item["workflow_history"].items():
            if isinstance(history, list) and workflow_comments:
                # Add comment as a new history entry
                comment_entry = {
                    "action": "comment",
                    "actor": "system",
                    "comments": workflow_comments,
                    "review_state": item["review_state"],
                    "time": datetime.now().isoformat()
                }
                history.append(comment_entry)
    
    yield item


async def process_workflow_transitions(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Process workflow transitions.
    
    This step handles the execution of pending workflow transitions
    that were stored during the main workflow processing.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Item with processed workflow transitions
    """
    
    if pending_transitions := item.pop("_pending_transitions", None):
        # Process each transition
        for transition in pending_transitions:
            transition_name = transition.get("name")
            transition_actor = transition.get("actor", "system")
            transition_comments = transition.get("comments", "")
            transition_time = transition.get("time", datetime.now().isoformat())
            
            # Add transition to workflow history
            if "workflow_history" not in item:
                item["workflow_history"] = {}
            
            for workflow_id, history in item["workflow_history"].items():
                if isinstance(history, list):
                    transition_entry = {
                        "action": transition_name,
                        "actor": transition_actor,
                        "comments": transition_comments,
                        "review_state": item["review_state"],
                        "time": transition_time
                    }
                    history.append(transition_entry)
    
    yield item


async def validate_workflow_states(
    item: t.PloneItem, metadata: t.MetadataInfo
) -> t.PloneItemGenerator:
    """Validate workflow states and ensure consistency.
    
    This step validates that workflow states are consistent and
    that required fields are present.
    
    Args:
        item: Plone item to process
        metadata: Metadata information for the transformation
        
    Yields:
        Item with validated workflow information
    """
    
    # Ensure review_state is present
    if not item.get("review_state"):
        content_type = item.get("@type", "Document")
        type_config = pb_config.types.get(content_type, {})
        default_state = type_config.get("default_state", "private")
        item["review_state"] = default_state
    
    # Validate workflow history structure
    if workflow_history := item.get("workflow_history", {}):
        for workflow_id, history in workflow_history.items():
            if not isinstance(history, list):
                # Convert to list if it's not already
                item["workflow_history"][workflow_id] = []
    
    # Ensure workflow field is set
    content_type = item.get("@type", "Document")
    type_config = pb_config.types.get(content_type, {})
    
    if workflow_name := type_config.get("workflow"):
        item["workflow"] = workflow_name
    
    yield item 