# nixhelm

This is a collection of helm charts in a nix-digestible format.

## Background

A short overview for those unfamiliar with the tools involved.

- [Kubernetes](https://kubernetes.io) applications are described by YAML
  manifests: deployments, services, config maps and so on. A single application
  usually needs a lot of them.
- [Helm](https://helm.sh) is a package manager for Kubernetes. A chart is a set of
  templated manifests plus a `values.yaml` of settings, which Helm renders into the
  YAML applied to a cluster. Charts are published to chart repositories.
- [Nix](https://nixos.org) builds from pinned, hash-checked inputs, so a build
  produces the same result on any machine. `helm repo update` gives no such
  guarantee, it moves to whatever version the repository serves at that moment.
- **nixhelm** stores chart versions and hashes in `charts/`, which makes a chart a
  regular nix input. Pinning nixhelm pins every chart in use. Versions are refreshed
  nightly, so updates arrive as commits to pull rather than at deploy time.
- nixhelm itself only provides the charts. Rendering them into manifests is done by
  [nix-kube-generators](https://github.com/farcaller/nix-kube-generators) at build
  time, see [Usage](#usage) below.

## Supported chart repositories

nixhelm supports both traditional HTTP helm chart repositories and OCI-compliant registries:

- **HTTP/HTTPS repositories** (ChartMuseum, traditional Helm repos)
- **OCI registries** (GitHub Container Registry, Docker Hub, Harbor, etc.)

If your chart is hosted in a git repo, remember that you can fetch it as a flake
input and pass to `buildHelmChart` [directly](https://github.com/nix-community/nixhelm/issues/10).

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

This will download the Argo CD helm chart to `result/`.

To build a chart, you should use the kube generators from
[github:farcaller/nix-kube-generators](https://github.com/farcaller/nix-kube-generators),
and just pass your chart to the `buildHelmChart` function. So for example to render
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
enable it in your nix installation.

Install cachix, either without flakes:

```sh
nix-env -iA cachix -f https://cachix.org/api/v1/install
```

or with flakes:

```sh
nix profile install nixpkgs#cachix
```

Then enable the cache:

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
repository and `CHART_NAME` is the name of the chart in the repository.

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
