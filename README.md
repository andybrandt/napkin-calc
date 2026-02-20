# Napkin Calculator

> Real-time back-of-the-envelope math for system design interviews — without the napkin.

Napkin Calculator is a desktop tool that lets you punch in a traffic rate, payload size,
or storage volume in **any** unit and instantly see the converted results across every
time window and data magnitude. No more fumbling with zeros on a whiteboard.

## Why?

During a system design interview you're expected to toss out estimates like
*"that's roughly 120 requests per second"* or *"about 1.5 PB per year"*.
Doing that mental arithmetic under pressure is error-prone.
Napkin Calculator keeps the math honest while you keep talking.

## Quick Start

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate    # Linux / macOS
# .venv\Scripts\activate     # Windows

# Install (with dev dependencies for testing)
pip install -e ".[dev]"

# Launch
napkin-calc
```

## Features

| Status | Feature | Description |
|--------|---------|-------------|
| Done | **Traffic & Throughput Engine** | Enter a rate in any time unit (per sec / min / hr / d / mo / y) — all others update instantly. |
| Done | **Exact / Estimate toggle** | Switch between precise binary math (1 KB = 1,024 B) and rounded napkin-friendly numbers (1 KB = 1,000 B). |
| Done | **Scientific notation** | Large values show their power-of-ten alongside the number, e.g. *1,000,000 (10^6)*. |
| Planned | **Data Volume Modeler** | Combine payload size with traffic rate to project storage over days, months, or years. |
| Planned | **Talking Points** | Auto-generated human-friendly summaries you can read aloud mid-interview. |
| Planned | **Scenario Save / Load** | Persist calculator state to JSON so you can build a library of practice scenarios. |
| Planned | **Delay-Bandwidth Product** | Calculate buffer sizes from latency and bandwidth inputs. |
| Planned | **Reference Tables** | Built-in HA "nines" and storage-latency cheat sheets. |

## Running Tests

```bash
python -m pytest tests/ -v
```

## Tech Stack

- **Python 3.12+**
- **PySide6 (Qt 6)** for the desktop UI
- **Decimal** arithmetic throughout for precision

## License

MIT
