# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

Docker Cluster Monitor is a TUI (Terminal User Interface) tool for monitoring Docker containers running on remote servers. It provides a live, color-coded view of container status, CPU usage, and memory consumption with automatic refresh every 5 seconds.

## Development Commands

### Code Quality & Linting
```bash
# Format code with ruff
ruff format .

# Check code quality and fix auto-fixable issues
ruff check . --fix

# Run all linting checks
ruff check .
```

### Building & Distribution
```bash
# Build the package (requires hatch)
python -m build

# Install in development mode
pip install -e .

# Test the CLI directly
python -m dockerclustermon my-host
```

### Running the Application
```bash
# After installation, use either command:
dockerstatus my-docker-host
ds my-docker-host

# With username
dockerstatus my-docker-host root

# With SSH config entry
dockerstatus --ssh-config my-host-alias

# Run with sudo on remote host
dockerstatus --sudo my-docker-host
```

## Architecture

This is a single-file Python application (`dockerclustermon/__init__.py`) with a focused architecture:

### Core Components
- **Typer CLI Framework**: Handles command-line argument parsing and help text
- **Rich TUI**: Provides live-updating table display with color coding
- **SSH Abstraction**: Manages remote command execution via SSH
- **Docker CLI Parsing**: Parses output from `docker ps` and `docker stats`
- **Threading Worker Pool**: Concurrent execution of Docker commands for performance

### Key Functions
- `live_status()`: Main entry point and TUI loop
- `build_table()`: Constructs the Rich table with container data
- `run_update()`: Coordinates threaded data collection
- `run_ps_command()`: Executes `docker ps` and parses output
- `run_stat_command()`: Executes `docker stats --no-stream` and parses output
- `run_free_command()`: Gets system memory information

### CLI Entry Points
The package exposes two console scripts via `pyproject.toml`:
- `dockerstatus` → `dockerclustermon:run_live_status`
- `ds` → `dockerclustermon:run_live_status` (shorter alias)

## Project Structure

```
dockerclustermon/
├── dockerclustermon/
│   └── __init__.py        # Single-file application (all logic)
├── pyproject.toml         # Package configuration and dependencies
├── ruff.toml             # Code quality configuration
├── README.md             # User documentation and install instructions
└── LICENSE               # MIT license
```

## Installation Methods

### For Development
```bash
# Clone and install in development mode
git clone <repo-url>
cd dockerclustermon
python -m pip install -e .
```

### For Users (from PyPI)
```bash
# Using uv (recommended)
uv tool install dockerclustermon

# Using pipx
pipx install dockerclustermon
```

## Technical Details

### Remote Execution
- Uses SSH to execute Docker commands on remote hosts
- Supports SSH config entries with `--ssh-config` flag
- Can run commands with sudo via `--sudo` flag
- Falls back to local execution for localhost/127.0.0.1

### Data Collection Strategy
- Runs three Docker commands concurrently using threads:
  1. `docker ps` - Container list and status
  2. `docker stats --no-stream` - CPU/memory usage
  3. `free -m` - System memory information
- Joins results by container name
- Applies color coding based on resource usage thresholds

### Color Coding Logic
- **CPU**: Green (≤5%), Cyan (5-25%), Red (>25%)
- **Memory**: Green (≤25%), Cyan (25-65%), Red (>65%)
- **Status**: Red for containers with "unhealthy" or "restart" in status

## Configuration

### Ruff Settings
- Line length: 120 characters
- Quote style: Single quotes
- Target Python version: 3.13
- Enabled rules: Pyflakes E and F codes
- Max complexity: 10

### Python Compatibility
- Minimum Python version: 3.10
- Tested on Python 3.10, 3.11, 3.12, 3.13

## Build & Release Process

```bash
# Bump version in dockerclustermon/__init__.py and pyproject.toml
# Build distribution packages
python -m build

# Upload to PyPI (maintainers only)
python -m twine upload dist/*
```