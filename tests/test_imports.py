"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from di_monitor.application import DiMonitorApplication
    assert DiMonitorApplication

def test_config():
    from di_monitor.app_config import DiMonitorConfig

    config = DiMonitorConfig()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from di_monitor.app_ui import DiMonitorUI
    assert DiMonitorUI

def test_state():
    from di_monitor.app_state import DiMonitorState
    assert DiMonitorState