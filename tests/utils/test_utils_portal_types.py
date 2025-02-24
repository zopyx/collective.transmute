from collective.transmute.utils import portal_types

import pytest


@pytest.mark.parametrize(
    "portal_type,expected",
    [
        ["File", "File"],
        ["Folder", "Document"],
        ["MyStrangeType", ""],
        ["Collection", "Document"],
    ],
)
def test_fix_portal_type(portal_type: str, expected: str):
    func = portal_types.fix_portal_type
    assert func(portal_type) == expected
