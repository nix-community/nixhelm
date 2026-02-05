# Changelog

All notable changes to this project will be documented in this file.

## 2026-02-05

### helmupdater 0.2.4

#### Fixed

- Fixed wrong version output in commit message in `update-all` action ([#85](https://github.com/nix-community/nixhelm/issues/85))

## 2026-01-11

### helmupdater 0.2.3

#### Changed

- Changed version parsing in `registry.get_versions()`:
  - Now skips invalid version strings during parsing and raises an error if all versions are invalid.
  - Filters out prerelease versions (alpha, beta, rc, dev) - only stable releases are returned.
- Changed version handling in `chart.update()` - now updates to the latest stable version only:
  - If the current version is higher than the latest available stable version, it will be downgraded.
  - This handles "yanked" versions and prevents prerelease versions from being selected.

## 2026-01-08

### helmupdater 0.2.2

#### Fixed

- Fixed chart version parsing.
- Fixed exception handling in `update-all` command.

#### Changed

- Changed chart version parsing from `semver` to `packaging.version` as it is more permissive.

### helmupdater 0.2.1

#### Fixed

- Fixed an error with running "git commit" on no changes. Now empty changes are skipped.

### General

#### Added

- Specified a default nix formatter (`nixfmt-tree`) in `flake.nix`.
- Added an ad-hoc single-chart update GitHub action (`update-chart`).

#### Changed

- `flake.nix`: Switched from `poetry2nix` to `uv2nix` (`poetry2nix` is currently unmaintained).
- Updated existing GitHub actions with the changes introduced in `helmupdater`.

### helmupdater 0.2.0

This is a complete rewrite of the `helmupdater` in a modular way.

#### Breaking Changes

- CLI options changed
  - `--rebuild` is renamed to `--build`
  - `--rehash_only` has been removed in favor of a separate `rehash` command.

#### Added

- Added support of OCI registries (🎉 [#1](https://github.com/nix-community/nixhelm/issues/1))
- Added registry services for end-to-end testing (see `tests/_infra`).
- Added test coverage.
- New CLI command: `build` to build a nix derivation.
- New CLI command: `rehash` to set a proper hash in the chart metadata file.

#### Changed

- Updated `pyproject.toml` to a modern format (PEP-621).
- Switched from `poetry` to `uv` for dependency management.
- Removed `bogusVersion` usage.
