"""Smoke tests for astrbot_plugin_zhouli."""

import importlib
from pathlib import Path


def test_main_module_importable() -> None:
    """Ensure the plugin main module can be imported."""
    module = importlib.import_module("main")
    assert module is not None
    assert hasattr(module, "ZhouLi")


def test_metadata_file_exists() -> None:
    """Ensure metadata.yaml is present and readable."""
    meta = Path(__file__).resolve().parent.parent / "metadata.yaml"
    assert meta.exists()
    text = meta.read_text(encoding="utf-8")
    assert "name: astrbot_plugin_zhouli" in text


def test_conf_schema_is_valid_json() -> None:
    """Ensure _conf_schema.json parses correctly."""
    import json

    schema = Path(__file__).resolve().parent.parent / "_conf_schema.json"
    assert schema.exists()
    data = json.loads(schema.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "command_prefix" in data
