from collective.transmute import _types as t
from pathlib import Path

import pytest


@pytest.fixture
def metadata() -> t.MetadataInfo:
    return t.MetadataInfo(path=Path(__file__))
