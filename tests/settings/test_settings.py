from collective.transmute import settings

import pytest


@pytest.mark.parametrize(
    "key,expected",
    [
        ["config.debug", bool],
        ["config.report", int],
        ["principals.default", str],
        ["principals.remove", list],
        ["pipeline.steps", list],
        ["pipeline.do_not_add_drop", list],
        ["review_state.filter.allowed", list],
        ["paths.cleanup", dict],
        ["paths.filter.allowed", set],
        ["paths.filter.drop", set],
    ],
)
def test_settings_pb_config_default(key: str, expected):
    value = settings.pb_config
    parts = key.split(".")
    for part in parts:
        value = getattr(value, part)
    assert isinstance(value, expected)


def test_settings_is_debug_default():
    assert settings.is_debug is False
