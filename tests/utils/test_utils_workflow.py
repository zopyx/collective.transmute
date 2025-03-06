import pytest


@pytest.fixture
def rewrite_settings(monkeypatch):
    settings = {
        "states": {
            "private": "private",
            "visible": "published",
        },
        "workflows": {
            "plone_workflow": "simple_publication_workflow",
        },
    }
    monkeypatch.setattr(
        "collective.transmute.utils.workflow.rewrite_settings", lambda: settings
    )


@pytest.fixture
def item(load_json_resource) -> dict:
    return load_json_resource("workflow.json")


def test_rewrite_workflow_history(rewrite_settings, item):
    from collective.transmute.utils import workflow

    func = workflow.rewrite_workflow_history
    result = func(item)
    assert result["review_state"] == "published"
    history = result["workflow_history"]
    assert "plone_workflow" not in history
    assert "simple_publication_workflow" in history
