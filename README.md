# DI Monitor

A Doover 2 device application that watches one Doovit digital input and raises
an alarm when the input stays in its alarm state for a configurable **hold
time**. Optionally, the alarm is only **armed** while a second digital input is
at a given level (for example "isolator power present"). The alarm shows as a
warning in the app's UI and, unless turned off, is sent as a Doover
notification.

`allow_many` is on: install it once per input you want to watch.

## How it works

- Every **Poll Period Seconds** (default 1 s) the app reads the input with
  `fetch_di` (and the arm input, if configured).
- The input is **active** when it reads at the **Alarm When** level.
- When it has been active, unbroken, for **Hold Seconds**, the alarm **trips**:
  the UI warning appears, `trip_count` goes up, and an `alarm` notification
  (severity Warn) is sent.
- While it stays active, the alarm is re-sent every **Renotify Seconds**.
  `0` means **never**: one notification per trip.
- When a tripped alarm returns to normal, a `cleared` notification (severity
  Info) is sent if **Notify On Clear** is on. A blip shorter than the hold time
  never sends anything, not even a clear.
- A read that fails (`fetch_di` returns `None` or raises) is **unknown**. The
  sample is skipped: the hold timer is neither reset nor tripped by it, and
  `di_read_ok` goes false. Wall time still passes, so a valid active reading
  afterwards counts from the original start.

### Arming

If **Arm DI Pin** is set, the alarm logic only runs while that input is at
**Arm DI Level**. While not armed:

- the hold timer is reset, so arming again starts the hold from zero;
- an active alarm is cleared **without a `cleared` notification**. Losing the
  arm condition (e.g. the isolator being switched off) is not the fault going
  away, so "back to normal" would be misleading. The UI status shows
  "Not armed".

If the arm input itself can't be read, the sample is skipped the same way as
an unreadable main input.

### Notifications off

With **Notifications Enabled** off, nothing is ever sent to the notifications
channel. The UI still shows the warning, alarm state and trip count. Use this
for status-only monitors.

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `di_name` | String | required | What the input is (e.g. "Compressor"). Used in the UI and messages. |
| `di_pin` | Integer 0-3 | required | Digital input to monitor. |
| `alarm_when` | `low` \| `high` | `low` | The level that counts as active. |
| `hold_seconds` | Number ≥ 0 | `30` | How long the input must stay active before the alarm trips. |
| `renotify_seconds` | Number ≥ 0 | `0` | Re-send interval while active. `0` = never. |
| `notify_on_clear` | Boolean | `true` | Send `cleared` when a tripped alarm returns to normal. |
| `notifications_enabled` | Boolean | `true` | When false, nothing is sent; the UI still warns. |
| `alarm_message` | String | `{di_name} active for longer than {hold_seconds} s` | Alarm notification and UI warning text. |
| `clear_message` | String | `{di_name} back to normal` | Cleared notification text. |
| `arm_di_pin` | Integer 0-3, optional | unset (always armed) | Input that arms the alarm. |
| `arm_di_level` | `low` \| `high` | `high` | Level of `arm_di_pin` at which the alarm is armed. |
| `poll_period_seconds` | Number 0.5-60 (advanced) | `1` | How often the input(s) are read. Hold timing is wall-clock, so a longer period only delays detection by up to one period; each read is a Doovit MCU round trip. |

Message placeholders: `{di_name}`, `{di_pin}`, `{hold_seconds}`,
`{active_seconds}`. Unknown placeholders are left as written.

## Tags

| Tag | Meaning |
|---|---|
| `di_state` | Last valid reading of the input (true = HIGH). |
| `di_read_ok` | False while the input (or arm input) can't be read. |
| `armed` | Whether the alarm logic is running. Always true without an arm input. |
| `alarm_active` | The alarm is tripped. |
| `active_seconds` | How long the input has been continuously active. |
| `trip_count` | Number of trips. Kept in `tag_values`, so it survives restarts. |
| `last_trip_at` | Time of the last trip, epoch milliseconds. |
| `status` | "Normal", "Active N s / hold H s", "ALARM: ...", "Not armed ...", "Input unreadable". |

## UI

A warning indicator (shown only while the alarm is tripped, with the alarm
message), status line, input state, armed state (only when an arm input is
set), alarm active, "Active For (hold H s)", trip count, last trip time and
whether the input is readable.

## Notifications

| Event | Severity | When |
|---|---|---|
| `alarm` | Warn | On trip, and every `renotify_seconds` while active (if > 0). |
| `cleared` | Info | When a tripped alarm returns to normal (if `notify_on_clear`). |

Neither is sent when `notifications_enabled` is false. Neither is sent when
the alarm is cleared by disarming.

## Example: Maxitool Porgera Station 8

Three installs. DI3 is wired to isolator power: when it is LOW the isolator
is off, and neither the compressor nor the oil cooler fan can start, so those
two alarms are armed only while DI3 is HIGH. DI0 and DI1 read LOW when the load
is running.

Compressor (`di_monitor_compressor`):

```json
{"di_name": "Compressor", "di_pin": 0, "alarm_when": "low",
 "hold_seconds": 30, "renotify_seconds": 0, "notify_on_clear": true,
 "arm_di_pin": 3, "arm_di_level": "high"}
```

Oil cooler fan (`di_monitor_oil_cooler_fan`):

```json
{"di_name": "Oil Cooler Fan", "di_pin": 1, "alarm_when": "low",
 "hold_seconds": 30, "renotify_seconds": 0, "notify_on_clear": true,
 "arm_di_pin": 3, "arm_di_level": "high"}
```

Isolator (`di_monitor_isolator`): UI warning only, no notifications:

```json
{"di_name": "Isolator", "di_pin": 3, "alarm_when": "low",
 "hold_seconds": 5, "notifications_enabled": false,
 "alarm_message": "Isolator is switched off: the compressor and oil cooler fan cannot run",
 "clear_message": "Isolator power restored"}
```

The hold times for the compressor and fan are placeholders until site
confirms them.

## Development

```bash
uv sync
uv run pytest
uvx ruff check . && uvx ruff format --check .
```

`uv run export-config`, `export-ui` and `export-notifications` write the
generated schemas into `doover_config.json` so you can inspect them. Don't
commit them: `doover app publish` generates them at publish time. Revert the
file afterwards.

`simulators/docker-compose.yml` runs the three Station 8 installs against the
platform interface's simulator driver (Linux / host networking).

CI is the shared `getdoover/workflows` `app.yml` (lint, format, schema
validation, tests, image smoke test, publish and release).

## Project structure

```
src/di_monitor/
├── __init__.py           entry point
├── application.py        loop: read inputs, feed HoldAlarm, notify, publish tags
├── hold_alarm.py         HoldAlarm + AlarmEvent (pure, clock passed in)
├── app_config.py         config schema
├── app_tags.py           tags
├── app_ui.py             UI
└── app_notifications.py  alarm / cleared notifications
tests/
├── harness.py            real app with fake fetch_di, tags, notifications, clock
├── test_hold_alarm.py
├── test_application.py
└── test_imports.py
```

## License

Apache 2.0. See `LICENSE`.
