from collective.transmute.steps import ids

import pytest


@pytest.mark.parametrize(
    "base_item,path,id_",
    [
        [{"@id": "http://localhost:8080/Plone/foo", "id": "foo"}, "/foo", "foo"],
        [{"@id": "http://localhost:8080/Plone/ foo", "id": " foo"}, "/foo", "foo"],
        [{"@id": "http://localhost:8080/Plone/_foo", "id": "_foo"}, "/foo", "foo"],
        [
            {"@id": "http://localhost:8080/Plone/_foo bar", "id": "_foo bar"},
            "/foo_bar",
            "foo_bar",
        ],
    ],
)
async def test_process_ids(metadata, base_item, path: str, id_: str):
    results = []
    async for item in ids.process_ids(base_item, metadata):
        results.append(item)
    assert len(results) == 1
    result = results[0]
    assert result["@id"] == path
    assert result["id"] == id_


@pytest.mark.parametrize(
    "id_,expected",
    [
        [" foo ", "foo"],
        ["__ foo __", "foo"],
        ["_document", "document"],
    ],
)
def test_fix_short_id(id_: str, expected: str):
    result = ids.fix_short_id(id_)
    assert result == expected
