# Docker Cluster Monitor - A TUI utility to monitor your docker containers

A TUI tool for a live view of your docker containers running on a remote server. Here's a graphic of it running (refreshes every 5 seconds or so automatically):

![](https://mkennedy-shared.nyc3.digitaloceanspaces.com/docker-status.gif)

Notice that it uses color to communicate outlier values. For example, low CPU is green, middle-of-the-road CPU is cyan, and heavy CPU usage is red. Similarly for memory. The memory limit column reflects the deploy>memory limit in Docker Compose for that container and the percentage reported is for the imposed memory limit rather than the machine physical memory limits.

## Usage

To use the tool, it has one command, `dockerstatus` with a shorter alias `ds`. If you are running a set of Docker containers (say via Docker Compose) on server `my-docker-host`, then just run:

```bash
dockerstatus my-docker-host
```

You can optionally pass the username if you're not logging in as `root`. Here is the full help text (thank you Typer):

```bash
 Usage: dockerstatus [OPTIONS] HOST [USERNAME]                          
╭─ Arguments ───────────────────────────────────────────────────────────╮
│ * host     TEXT       The server DNS name or IP address (e.g. 91.7.5.1│ 
│                       or google.com). [default: None]  [required]     │
│   username [USERNAME] The username of the ssh user for interacting    │
│                       with the server. [default: root]                │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────╮
| --ssh-config    Whether the host is a SSH config entry or not.        |
| --sudo          Whether to run as the super user or not.              |
│ --help          Show this message and exit.                           │
╰───────────────────────────────────────────────────────────────────────╯
```

## Installation

This package is available on PyPI as dockerclustermon. However, it is ideally used as a CLI tool 
and not imported into programs. As such, using **uv** or **pipx** will be most useful. Take your pick:

### uv

```bash
uv tool install dockerclustermon
```

Of course this requires that you have 
[uv installed](https://docs.astral.sh/uv/getting-started/installation/) 
and in the path.

### pipx

```bash
pipx install dockerclustermon
```

And this requires that you have [pipx installed](https://pipx.pypa.io/stable/installation/) 
and in the path.


Compatibility
-------------

Docker Cluster Monitor has been tested against Ubunutu Linux. It should work on any system that 
supports SSH and has the Docker CLI tools installed. Note that it does **not** work on the local 
machine at the moment. PRs are welcome. ;)