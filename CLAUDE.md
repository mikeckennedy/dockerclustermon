# CLAUDE.md

Guidance for Claude Code (and other AI agents) when working in this repository.

> This file supersedes the older `WARP.md`, which drifted out of date. Everything
> below was verified against the source in `dockerclustermon/__init__.py`.

## Overview

Docker Cluster Monitor is a terminal (TUI) tool that shows a live, color-coded
dashboard of Docker containers running on a **remote** server, reached over SSH.
It renders container status, CPU %, memory usage/limit, and whole-machine memory,
continuously refreshing in place.

- Published on PyPI as `dockerclustermon`; installed as a standalone CLI, not a library.
- Two console commands, both mapping to `dockerclustermon:run_live_status`:
  - `dockerstatus <host>`
  - `ds <host>` (short alias)

## Project layout

This is effectively a **single-file application**. All logic lives in one module:

```
dockerclustermon/
├── dockerclustermon/
│   └── __init__.py     # ENTIRE application — CLI, SSH, parsing, rendering
├── pyproject.toml      # Package metadata, deps, console scripts (hatchling + hatch-vcs)
├── uv.lock             # uv-managed lockfile (this is a uv project)
├── ruff.toml           # Lint/format config
├── pyrefly.toml        # Type-checker config (see caveat below)
├── change-log.md       # Keep-a-Changelog history — UPDATE THIS on user-visible changes
├── README.md           # User-facing docs
├── ERROR_HANDLING.md   # Deep-dive notes on the error/retry design
├── SSH_OPTIMIZATION.md  # Deep-dive notes on the Paramiko persistent-connection work
└── LICENSE             # MIT
```

There is currently **no test suite and no CI**. The `pyproject.toml` build
excludes reference `/tests`, `/example`, and `/readme_resources`, but those
directories do not exist in the working tree.

## Development

This is a `uv` project (there's a `uv.lock`). Prefer `uv`:

```bash
uv sync                      # create/refresh the environment from uv.lock
uv run ds localhost --no-ssh # run from source against the local Docker daemon

# Lint & format (ruff)
uv run ruff format .         # format (single quotes, 120 cols)
uv run ruff check .          # lint (rules: E, F, I)
uv run ruff check . --fix    # lint + autofix

# Type check (config present; see caveat)
uv run pyrefly check
```

Running from source without installing: `python dockerclustermon/__init__.py <host>`
works because of the `if __name__ == '__main__'` guard. Note that
`python -m dockerclustermon` does **not** work — there is no `__main__.py`.

### Config notes

- **ruff** (`ruff.toml`): line length 120, single-quote style, `target-version = py313`,
  rules `E, F, I`, mccabe `max-complexity = 10`.
- **pyrefly** (`pyrefly.toml`): appears to be a copied generic template — its
  `search-path` points at `app`, `daemons/transcript_daemon/src`, `typings` and it
  references `quart`, none of which exist here. Treat it as not yet tailored to this
  project; don't trust its results blindly.
- **Python**: `requires-python >= 3.10`; classifiers advertise 3.10–3.14.

## Architecture & data flow

Entry point `run_live_status()` → `typer.run(live_status)`.

`live_status()` (the CLI command, argument annotations at the top of the module):
1. Handles `--version`, sets the process title via `setproctitle` (so it shows as
   `dockerclustermon` in Activity Monitor / `ps`).
2. Auto-forces `--no-ssh` when host is `localhost`, `127.0.0.1`, or `::1`.
3. Renders one table under a spinner, then enters a `rich.live.Live` loop that calls
   `build_table()` over and over.

**Refresh cadence:** the live loop is a tight `while True` with **no sleep**. The
effective refresh rate is bounded by how long the remote commands take — chiefly
`docker stats --no-stream`, which inherently blocks ~1–2s. (The old WARP.md claim of
"every 5 seconds" was wrong.) The only explicit `time.sleep(1)` calls are on error
retry paths inside `build_table()`.

`build_table()` → `run_update()` → `process_results()`:

- **`run_update()`** gets/reuses a persistent Paramiko SSH client, then spawns **three
  daemon threads** that run concurrently:
  - `run_stat_command()`  → `docker stats --no-stream`
  - `run_ps_command()`    → `docker ps`
  - `run_free_command()`  → `free -m` (whole-machine memory)

  Threads are joined with a `timeout + 5s` buffer. Each worker writes into a shared,
  **module-level global `results` dict** (`ps`, `stat`, `free`, `error`) rather than
  returning values up the stack. If any worker set `results['error']`, `run_update()`
  re-raises it.
- **`process_results()`** joins `ps` and `stat` rows by container `NAME`
  (`join_results()`), normalizes them (`reduce_lines()`), and computes totals
  (`total_percent()`, `total_sizes()`).

### Output parsing is fixed-width, not columnar-split

The docker/free output is parsed by **column start position**, not by splitting on
whitespace (container names and statuses contain spaces):

- `parse_ps_header()` / `parse_stat_header()` / `parse_free_header()` locate each known
  column name in the header line (case-insensitively) to get its character offset.
- `parse_line()` then slices each data row between consecutive offsets.

This is fragile by nature, so header parsers raise **detailed** `ValueError`s (showing
actual vs. expected columns) when Docker's format differs across versions/platforms.
If you touch parsing, preserve those diagnostics.

### Platform differences (Linux/Mac vs. Windows Docker)

Windows Docker's `docker stats` omits `MEM USAGE / LIMIT`, `MEM %`, and `PIDS` and
instead emits `PRIV WORKING SET`. Handled by:
- `parse_stat_header()` — splits columns into *required* (all platforms) and *optional*
  (platform-specific, included only if present).
- `normalize_stat_dict()` — maps `PRIV WORKING SET` → `MEM USAGE`, fills missing keys
  with `N/A`.
- `split_mem()` — splits `MEM USAGE / LIMIT` into `MEM USAGE` + `MEM LIMIT`; no-op when
  the key is absent (Windows).

Unavailable metrics render as a dimmed `N/A` rather than crashing.

### Rendering / color coding

- Rows are sorted youngest-uptime-first via `get_seconds_key_from_string()` (parses
  "3 minutes", "About an hour", etc.), then by name.
- `color_number()` thresholds:
  - **CPU %**: green `≤5`, cyan `≤25`, red `>25`
  - **Mem %**: green `≤25`, cyan `≤65`, red `>65`
  - `N/A` renders dim.
- `color_text()` marks a status bold-red if it contains `unhealthy` or `restart`.
- The table ends with a blank row, a **Totals** row (summed CPU % and memory), and a
  **Server** row (whole-machine memory from `free -m`).

## CLI options (all defined in `live_status`)

| Argument / flag | Default | Purpose |
|---|---|---|
| `host` (positional) | `localhost` | Server DNS name or IP |
| `username` (positional) | `root` | SSH user |
| `--no-ssh` | off | Run docker commands locally instead of over SSH |
| `--ssh-config` | off | Treat `host` as an entry in `~/.ssh/config` |
| `--sudo` | off | Prefix remote docker commands with `sudo` |
| `--timeout` | `30` | Per-command timeout (seconds) before showing an error/retry |
| `--debug` | off | Capture full stdout/stderr; **re-raise errors and exit** instead of showing retry rows |
| `--version` / `-v` | — | Print version and exit |

## SSH execution model

- `docker`/`free` commands run over a **single persistent Paramiko SSH connection**
  (`get_ssh_client()` caches it in the module global `ssh_client`, testing
  `transport.is_active()` before reuse). This replaced per-command `ssh` subprocess
  spawns — see `SSH_OPTIMIZATION.md`.
- `run_command_with_debug()` is the unified runner: local `subprocess.run()` when
  `no_ssh`, else `run_ssh_command()` over Paramiko. A missing SSH client when SSH is
  required raises `ConnectionError` (deliberately **not** falling back to local, which
  would produce confusing output).
- `close_ssh_client()` is called on `KeyboardInterrupt` (Ctrl-C prints `kthxbye!`).

## Error handling philosophy

See `ERROR_HANDLING.md` for the full rationale. In short:

- **Normal mode:** transient failures (timeout, connection error, unexpected exceptions)
  render an in-table "Error … Retrying" row, sleep briefly, and continue the live loop
  so a flaky network self-heals. A `CalledProcessError` returns `None` and stops the loop.
- **`--debug` mode:** every error is **re-raised** to the top level and the process exits
  with full stdout/stderr and a traceback — use this when diagnosing.
- `free`-not-found (e.g. non-Linux remote) is swallowed so the container table still
  renders with the Server memory row degraded.

## Conventions / gotchas

- Single quotes everywhere (ruff-enforced).
- Shared mutable module globals (`results`, `workers`, `ssh_client`, `console`,
  `DEBUG_MODE`) are the intended design for this small tool — worker threads mutate
  `results` in place. Keep that in mind before "cleaning it up."
- **Update `change-log.md`** (Keep-a-Changelog format, includes a "Files:" line per
  entry) for any user-visible change.
- `__version__` is read at runtime from installed package metadata
  (`importlib.metadata.version`), so the version lives in `pyproject.toml` — there is no
  hardcoded version string in the module to bump.

## Release

- Version is set in `pyproject.toml` (`[project].version`).
- Build with the hatchling backend (`hatch-vcs` is present): `uv build`.
- Publish to PyPI: `uv publish` (maintainers only).
- Record the change in `change-log.md`.
