# Docker Cluster Monitor

**Stop SSH-ing into servers just to check container status.**

Get a live, color-coded dashboard of all your Docker containers across remote servers-right from your terminal. See CPU, memory, and health at a glance, updated automatically every few seconds.

![Docker Cluster Monitor in action](https://mkennedy-shared.nyc3.digitaloceanspaces.com/docker-status.gif)

## Why Docker Cluster Monitor?

**⚡ Save Time**: No more logging into servers to run `docker stats` or `docker ps`  
**👀 Instant Clarity**: Color-coded metrics show problems at a glance  
**🔄 Stay Informed**: Auto-refreshing dashboard keeps you updated  
**🚀 Zero Configuration**: Just point it at your server and go

## See Everything at a Glance

**Smart color coding** helps you spot issues instantly:
- 🟢 **Green**: Healthy, low resource usage
- 🔵 **Cyan**: Moderate load-everything's fine
- 🔴 **Red**: High CPU or memory usage-time to investigate

Memory percentages reflect your Docker Compose deployment limits, so you know exactly how close each container is to its configured threshold-not just the physical machine limits.

## Quick Start

### Install (choose one)

**Using uv** (recommended):
```bash
uv tool install dockerclustermon
```

**Using pipx**:
```bash
pipx install dockerclustermon
```

> **Note**: Make sure you have [uv](https://docs.astral.sh/uv/getting-started/installation/) or [pipx](https://pipx.pypa.io/stable/installation/) installed first.

### Monitor Your Containers

Run `dockerstatus` (or the shorter `ds` alias) with your server hostname:

```bash
dockerstatus my-docker-host
```

That's it! You now have a live dashboard of your containers, refreshing automatically.

## How to Use

### Basic Usage

Monitor containers on a remote server:
```bash
dockerstatus server.example.com
```

Specify a different SSH user (defaults to `root`):
```bash
dockerstatus server.example.com myuser
```

Use with SSH config entries:
```bash
dockerstatus my-server --ssh-config
```

Run with sudo privileges:
```bash
dockerstatus server.example.com --sudo
```

### Complete Command Reference

```bash
 Usage: dockerstatus [OPTIONS] HOST [USERNAME]                          
╭─ Arguments ───────────────────────────────────────────────────────────╮
│ * host     TEXT       The server DNS name or IP address (e.g. 91.7.5.1│ 
│                       or google.com). [default: None]  [required]     │
│   username [USERNAME] The username of the SSH user for interacting    │
│                       with the server. [default: root]                │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────╮
│ --ssh-config          Whether the host is a SSH config entry or not.  │
│ --sudo                Whether to run as the super user or not.        │
│ --help                Show this message and exit.                     │
╰───────────────────────────────────────────────────────────────────────╯
```

## System Requirements

Docker Cluster Monitor works on any system that supports SSH and has Docker CLI tools installed on the remote server.

**Tested on**: Ubuntu Linux  
**Should work on**: Most Linux distributions and Unix-like systems  
**Current limitation**: Does not work on the local machine (remote servers only)

> **Want local support?** Contributions welcome! PRs accepted.

## About

Docker Cluster Monitor is available on [PyPI](https://pypi.org/project/dockerclustermon/) as `dockerclustermon`. While it's published as a Python package, it's designed as a standalone CLI tool rather than a library to import into your programs.
