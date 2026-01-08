{
  description = "A collection of kubernetes helm charts in a nix-digestable format.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    flake-utils.url = "github:numtide/flake-utils";

    haumea = {
      url = "github:nix-community/haumea/v0.2.2";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nix-kube-generators.url = "github:farcaller/nix-kube-generators";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      haumea,
      nixpkgs,
      flake-utils,
      nix-kube-generators,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      ...
    }:
    {
      chartsMetadata = haumea.lib.load {
        src = ./charts;
        transformer = haumea.lib.transformers.liftDefault;
      };

      charts =
        { pkgs }:
        let
          kubelib = nix-kube-generators.lib { inherit pkgs; };
          trimBogusVersion = attrs: builtins.removeAttrs attrs [ "bogusVersion" ];
        in
        haumea.lib.load {
          src = ./charts;
          loader = { ... }: p: kubelib.downloadHelmChart (trimBogusVersion (import p));
          transformer = haumea.lib.transformers.liftDefault;
        };
    }
    // flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python314;
        workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
        pythonBase = pkgs.callPackage pyproject-nix.build.packages { inherit python; };
        overlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };
        pythonSet = pythonBase.overrideScope (
          pkgs.lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
          ]
        );

        virtualenv = pythonSet.mkVirtualEnv "nixhelm-venv" workspace.deps.default;
      in
      {
        chartsDerivations = self.charts { inherit pkgs; };

        packages = {
          helmupdater = virtualenv;
          default = self.packages.${system}.helmupdater;
        };

        apps = {
          helmupdater = {
            type = "app";
            program = "${self.packages.${system}.helmupdater}/bin/helmupdater";
          };

          default = self.apps.${system}.helmupdater;
        };

        formatter = pkgs.nixfmt-tree;

        devShell =
          let
            editableOverlay = workspace.mkEditablePyprojectOverlay {
              root = "$REPO_ROOT";
            };
            editablePythonSet = pythonSet.overrideScope editableOverlay;
            devVirtualenv = editablePythonSet.mkVirtualEnv "nixhelm-dev-venv" workspace.deps.all;
          in
          pkgs.mkShell {
            packages = [
              devVirtualenv
              pkgs.nixfmt-tree
              pkgs.uv
              pkgs.ruff
              pkgs.kubernetes-helm
              pkgs.crane
              pkgs.curl
            ];

            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = editablePythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };

            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
            '';
          };
      }
    );
}
