# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added `--debug` CLI flag to enable verbose output for diagnosing SSH and command execution issues
- New `run_command_with_debug()` helper function that captures both stdout and stderr from subprocess commands
- Debug mode displays stderr output in real-time (in yellow) when it occurs
- Error messages now include full stdout/stderr output when debug mode is enabled
- Files: `dockerclustermon/__init__.py`

### Changed
- Replaced `subprocess.check_output()` with `subprocess.run()` for better error handling and stderr capture
- Updated `run_free_command()`, `run_stat_command()`, and `run_ps_command()` to use new debug helper
- Files: `dockerclustermon/__init__.py`

### Deprecated
- 

### Removed
- 

### Fixed
- Fixed timeout handling to prevent indefinite hanging when SSH connections timeout or fail
- Added timeout to thread join operations (timeout + 5 seconds buffer) in `run_update()`
- All command functions (`run_stat_command`, `run_ps_command`, `run_free_command`) now properly catch `TimeoutExpired` exceptions
- Improved debug output to show when threads don't complete within expected timeframe
- Files: `dockerclustermon/__init__.py`

### Security
-

---

## [0.2.7] - 2025-11-03

### Changed
- Rewrote README.md with user-centric, benefit-driven approach
- Improved information hierarchy: problem → solution → quick start → details
- Set running process name to **dockerclustermon** (was **python**)
- Simplified installation and usage instructions
- Files: `README.md`
- Set default timeout value to 30 seconds for the `--timeout` CLI option
- Changed timeout parameter type from `Optional[int]` to `int` throughout the codebase
- Files: `dockerclustermon/__init__.py`

---

## [0.2.6] - 2025-10-16

### Added
- Added `--timeout` option to specify a timeout (in seconds) for server responses
- Displays error message if server fails to respond within the specified timeout period
- Files: `dockerclustermon/__init__.py`

### Fixed
- Improved error messages for "substring not found" errors on Windows and other platforms
- Added detailed diagnostic output showing actual vs expected Docker command headers when parsing fails
- Enhanced error handling in `parse_free_header`, `parse_stat_header`, and `parse_ps_header` functions
- Made header parsing case-insensitive to handle Docker version differences across platforms
- Replaced `.index()` with `.find()` for more robust error detection
- Files: `dockerclustermon/__init__.py`

### Notes
- Thank you @sanders41 for the timeout feature PR

---

## [0.2.5] - 2025-10-04

### Fixed
- Fixed "unsupported operand type(s) for +=: 'int' and 'str'" error that occurred when docker stats returned unexpected memory unit formats or malformed data
- Added handling for bare bytes ('B') unit in memory values
- Added error handling for malformed percentage values
- Files: `dockerclustermon/__init__.py` (functions: `total_sizes`, `total_percent`)

---

## [0.2.4] - 2025-10-04

### Added
- Loading spinner with version info displayed during app startup and initial data loading
- Multi-line startup display showing "Docker Cluster Monitor v0.2.4" followed by "Loading..." with spinner

### Fixed
- `--version` flag now works correctly when installed via pipx or uv tool

---

## [0.2.2] - 2024-11-22

### Changed
- Enhanced the ability to run locally without SSH
- Now works on macOS

### Notes
- Thank you @sanders41 for the PR

---

## [0.2.1] - 2024-11-22

### Added
- Support for reporting KB usage of memory in containers (previously was MB or above)

### Notes
- Thank you @sanders41

---

## [0.2.0] - 2024-11-21

### Added
- Initial release - Hello world

---

## Template for Future Entries

<!--
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features or capabilities
- Files: `path/to/new/file.ext`, `another/file.ext`

### Changed
- Modifications to existing functionality
- Files: `path/to/modified/file.ext` (summary if many files)

### Deprecated
- Features that will be removed in future versions
- Files affected: `path/to/deprecated/file.ext`

### Removed
- Features or files that were deleted
- Files: `path/to/removed/file.ext`

### Fixed
- Bug fixes and corrections
- Files: `path/to/fixed/file.ext`

### Security
- Security patches or vulnerability fixes
- Files: `path/to/security/file.ext`

### Notes
- Additional context or important information
- Major dependencies updated
- Breaking changes explanation
-->
