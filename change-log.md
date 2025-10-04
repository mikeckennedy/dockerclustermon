# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
-

### Changed
-

### Deprecated
- 

### Removed
- 

### Fixed
- 

### Security
-

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
