# helmupdater

Helm chart version management for Nix.

## Usage

See `helmupdater --help` for additional details.

Here is a quick overview of commands:

* `init` Initialize a new chart in the repository.
* `update` Update an existing chart to the latest version.
* `update-all` Update all existing charts to their latest versions.
* `rehash` Update the hash for an existing chart without changing the version.
* `build` Build a nix derivation of an existing chart.

Verbosity level can be controlled by an environment variable `LOG_LEVEL`. Available levels:
* `DEBUG`
* `INFO`
* `WARNING`
* `ERROR`
* `CRITICAL`

Global option `-v` / `--verbose` can be used to enable debug logging.

### Examples

```bash
# Initialize a new chart
helmupdater init \
  https://prometheus-community.github.io/helm-charts \
  prometheus-community/prometheus \
  --commit

# Update a single chart
helmupdater update prometheus-community/prometheus --commit --build

# Update all charts with debug logging
helmupdater -v update-all --commit

# Update all charts (using env var for logging)
LOG_LEVEL=DEBUG helmupdater update-all --commit
```

## Notes

### Git Tracking

Most commands have `--commit` flag. It is used to invoke `git add / git commit` at the end of the command execution. There are two main reasons for it.

* Most of the operations on chart metadata files (`charts/`) involve running `nix`. As such, file for the specific chart should be tracked by git.
* `helmupdater` is mostly executed by CI, and any version updates should be committed and pushed to the repo. This simplifies the CI pipeline definition.

### Build and CI

`build` action primarily is used in CI to build the chart and push it to the binary cache (Cachix).

### Rehash

During chart update, chart hash is computed and stored in the chart metadata file. If chart publisher at some point replaces the chart without changing a version, hash mismatch in `nix` will prevent chart from being used.

If such an update was intentional, it can be resolved by removing the chart and running `init` again, or by simply running `rehash` command.
