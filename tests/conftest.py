from pathlib import Path

import json
import pytest


RESOURCES = Path(__file__).parent / "_resources"


@pytest.fixture(scope="session")
def load_json_resource():
    def func(filename: str) -> dict:
        path = RESOURCES / filename
        return json.loads(path.read_text())

    return func
