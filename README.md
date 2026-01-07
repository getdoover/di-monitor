# DI Monitor

A Doover device application that monitors digital and analog inputs for state changes and sends configurable notifications when triggered.

## Overview

DI Monitor watches a specified input channel and detects transitions between triggered and untriggered states. When a trigger event occurs, it can send alert messages, track trigger counts, and measure how long the input remains in the triggered state.

**Common use cases:**
- Pump fault monitoring
- Door/window sensor alerts
- Equipment alarm detection
- Industrial equipment state tracking

## Features

- Monitor digital inputs (rising/falling edge detection)
- Monitor analog inputs with voltage thresholds (12V or 24V modes)
- Configurable alert messages on trigger and untrigger events
- Real-time duration tracking during trigger events
- Cumulative statistics (total trigger count and duration)
- Persistent state across restarts via Doover tags

## Configuration

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `di_name` | string | Yes | - | Display name for the input being monitored |
| `di_channel` | integer | Yes | - | Channel number to monitor (0+) |
| `di_triggered_state` | enum | No | `rising` | Trigger condition: `rising`, `falling`, `VI+`, or `VI-` |
| `send_triggered_alert` | boolean | No | `true` | Send alert when input is triggered |
| `send_untriggered_alert` | boolean | No | `false` | Send alert when input returns to untriggered |
| `alert_message` | string | Yes | - | Message to send on trigger |
| `alert_complete_message` | string | Yes | - | Message to send on untrigger |
| `voltage_state` | enum | No | `24V` | Voltage mode for analog inputs: `12V` or `24V` |
| `show_triggered_count` | boolean | Yes | - | Display trigger count in UI |
| `show_triggered_duration` | boolean | No | `true` | Display duration in UI |

### Example Configuration

```json
{
    "di_name": "Pump Fault",
    "di_channel": 0,
    "di_triggered_state": "VI+",
    "send_triggered_alert": true,
    "send_untriggered_alert": false,
    "alert_message": "Pump has just entered fault state",
    "alert_complete_message": "Pump is no longer faulting",
    "voltage_state": "12V",
    "show_triggered_count": true,
    "show_triggered_duration": true
}
```

### Trigger States

**Digital Inputs:**
- `rising` - Trigger when input goes HIGH
- `falling` - Trigger when input goes LOW

**Analog Inputs:**
- `VI+` - Trigger when voltage rises above threshold
- `VI-` - Trigger when voltage falls below threshold

Analog thresholds:
- 12V mode: 8V threshold
- 24V mode: 18V threshold

## Project Structure

```
di-monitor/
├── src/di_monitor/
│   ├── __init__.py          # Entry point
│   ├── application.py       # Main application logic
│   ├── app_config.py        # Configuration schema
│   ├── app_ui.py            # UI variable definitions
│   └── utils.py             # Utility functions
├── tests/
│   └── test_imports.py      # Test suite
├── simulators/
│   ├── sample/              # Sample simulator for testing
│   ├── docker-compose.yml   # Simulator orchestration
│   └── app_config.json      # Sample configuration
├── Dockerfile               # Production container build
├── pyproject.toml           # Project dependencies
├── doover_config.json       # Doover app metadata
└── README.md
```

## Prerequisites

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager
- Docker and Docker Compose (for containerized deployment)
- Doover CLI (`pydoover`)

## Development

### Install Dependencies

```bash
uv sync --all-extras --dev
```

### Run Locally

```bash
doover app run
```

### Run Tests

```bash
uv run pytest tests/
```

### Linting

```bash
uv run ruff check .
uv run ruff format --check .
```

## Simulator

The `simulators/` directory provides a testing environment with a sample data source.

```bash
cd simulators/
docker-compose up
```

This starts both the DI Monitor application and a simulator that generates sample input values.

## Deployment

### Build Docker Image

```bash
docker build -t di-monitor .
```

The Dockerfile supports multi-architecture builds (linux/amd64, linux/arm64).

### CI/CD

The repository includes GitHub Actions workflows:

- **lint-and-test.yml** - Runs on all branches except main
- **build-image.yml** - Builds and pushes to `ghcr.io/getdoover/di-monitor` on main branch

## How It Works

1. **Setup Phase**: The application initializes, loads persisted statistics from tags, and fetches the initial input state.

2. **Main Loop**: Every second, the application:
   - Reads the current input value
   - Detects state transitions
   - Updates duration counters for active triggers
   - Handles missed pulse events via fallback detection

3. **On Trigger**: When the input enters the triggered state:
   - Increments the trigger count
   - Publishes an alert to the `significantEvent` channel (if enabled)
   - Starts tracking trigger duration

4. **On Untrigger**: When the input returns to normal:
   - Calculates elapsed trigger duration
   - Adds to cumulative triggered time
   - Publishes an untrigger alert (if enabled)
   - Persists statistics to tags

## UI Variables

The application exposes the following UI variables:

| Variable | Type | Description |
|----------|------|-------------|
| `di_state` | Boolean | Current input state (true = triggered) |
| `last_triggered_duration` | Text | Duration of current trigger event (HH:MM:SS) |
| `triggered_duration` | Text | Total accumulated trigger time (HH:MM:SS) |
| `triggered_count` | Numeric | Total number of trigger events (optional) |

## License

Proprietary - Doover
