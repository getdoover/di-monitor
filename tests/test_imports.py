"""Imports, schema shape and declarations."""


def test_import_app():
    from di_monitor.application import DiMonitorApplication

    assert DiMonitorApplication.config_cls is not None
    assert DiMonitorApplication.tags_cls is not None
    assert DiMonitorApplication.ui_cls is not None
    assert DiMonitorApplication.notifications_cls is not None


def test_config_schema():
    from di_monitor.app_config import DiMonitorConfig

    schema = DiMonitorConfig.to_schema()
    props = schema["properties"]
    for key in (
        "di_name",
        "di_pin",
        "alarm_when",
        "hold_seconds",
        "renotify_seconds",
        "notify_on_clear",
        "notifications_enabled",
        "alarm_message",
        "clear_message",
        "arm_di_pin",
        "arm_di_level",
    ):
        assert key in props, key
    assert set(schema["required"]) >= {"di_name", "di_pin"}
    assert "arm_di_pin" not in schema["required"]
    assert props["di_pin"]["minimum"] == 0 and props["di_pin"]["maximum"] == 3
    assert props["alarm_when"]["default"] == "low"
    assert props["hold_seconds"]["default"] == 30.0
    assert props["renotify_seconds"]["default"] == 0.0
    assert props["notifications_enabled"]["default"] is True
    assert props["arm_di_level"]["default"] == "high"


def test_tags():
    from di_monitor.app_tags import DiMonitorTags

    for name in (
        "di_state",
        "di_read_ok",
        "alarm_active",
        "active_seconds",
        "armed",
        "trip_count",
        "last_trip_at",
    ):
        assert hasattr(DiMonitorTags, name)


def test_notifications():
    from di_monitor.app_notifications import DiMonitorNotifications

    schema = DiMonitorNotifications().to_schema()
    assert schema["alarm"]["severity"] == "Warn"
    assert schema["cleared"]["severity"] == "Info"


def test_ui():
    from pydoover.ui import UI

    from di_monitor.app_ui import DiMonitorUI

    assert issubclass(DiMonitorUI, UI)


def test_doover_config_has_no_generated_schemas():
    import json
    from pathlib import Path

    data = json.loads((Path(__file__).parents[1] / "doover_config.json").read_text())[
        "di_monitor"
    ]
    assert data["allow_many"] is True
    assert data["depends_on"] == ["platform_interface"]
    for block in ("config_schema", "ui_schema", "notification_schema"):
        assert block not in data


def test_simulator_configs_load():
    import json
    from pathlib import Path

    from di_monitor.app_config import DiMonitorConfig

    sims = Path(__file__).parents[1] / "simulators"
    for name in ("compressor", "fan", "isolator"):
        data = json.loads((sims / f"{name}_config.json").read_text())
        config = DiMonitorConfig()
        config._inject_deployment_config(data)
        assert config.di_pin.value in (0, 1, 3)
