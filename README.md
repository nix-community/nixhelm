# nixhelm

This is a collection of helm charts in a nix-digestible format.

## Supported chart repositories

Nixhelm supports both traditional HTTP helm chart repositories and OCI-compliant registries:

- **HTTP/HTTPS repositories** (ChartMuseum, traditional Helm repos)
- **OCI registries** (GitHub Container Registry, Docker Hub, Harbor, etc.)

If your chart is hosted in a git repo, remember that you can fetch it as a flake
input and pass to `buildHelmChart` [directly](https://github.com/farcaller/nixhelm/issues/10).

## Outputs

The flake has the following outputs:

`chartsMetadata.${repo}.${chart}` contains the metadata about a specific chart.

`chartsDerivations.${system}.${repo}.${chart}` contains the derivations producing
the charts.

`charts { pkgs = ... }.${repo}.${chart}` a shortcut for the above that doesn't
depend on the nixpkgs input and allows to specify any nixpkgs.

The charts are updated nightly.

## Usage

```sh
nix build .#chartsDerivations.x86_64-linux."argoproj"."argo-cd"
```

Will download the Argo CD helm chart to `result/`.

To build a chart, you should use the kube generators from
[github:farcaller/nix-kube-generators](https://github.com/farcaller/nix-kube-generators),
and just pass your chart to the `buildCharts` function. So for example to render
the Argo CD chart:

```nix
      argo = (kubelib.buildHelmChart {
        name = "argo";
        chart = (nixhelm.charts { inherit pkgs; }).argoproj.argo-cd;
        namespace = "argo";
      });
```

If you want to use this setup within Argo CD, check out [cake](https://github.com/farcaller/cake).

## Using the cache

This repository and all the charts within are publicly cached at `cachix` as
[nixhelm](https://app.cachix.org/cache/nixhelm). Here's how you can quickly
enable it in your nix installation:

### Without flakes

```sh
nix-env -iA cachix -f https://cachix.org/api/v1/install
```

### With flakes

```sh
nix profile install nixpkgs#cachix
```

### Then enable the cache

```sh
cachix use nixhelm
```

Alternatively, manually add this to `/etc/nix/nix.conf`:

```nix
substituters = https://cache.nixos.org https://nixhelm.cachix.org
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= nixhelm.cachix.org-1:esqauAsR4opRF0UsGrA6H3gD21OrzMnBBYvJXeddjtY=
```

## Adding new charts

Clone the repository and run the following command from within it:

```sh
nix run .#helmupdater -- init $REPO $REPO_NAME/$CHART_NAME --commit
```

Where `REPO` is the URL to the chart repository, `REPO_NAME` is the short name for the
repository and the `CHART_NAME` is the name of the chart in the repository.

### HTTP Repository Example

If you want to add [prometheus](https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus):

```sh
nix run .#helmupdater -- init "https://prometheus-community.github.io/helm-charts" prometheus-community/prometheus --commit
```

### OCI Registry Example

For charts hosted in OCI registries, use the `oci://` scheme:

```sh
nix run .#helmupdater -- init "oci://ghcr.io/myorg/charts" myorg/nginx --commit
```

The command will create the properly formatted commit that you can then submit
as a pull request to the repo.

## License

Apache-2.0
