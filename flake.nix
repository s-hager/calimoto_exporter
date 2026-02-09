{
  description = "react native flake";

  inputs.nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";

  outputs = { self, nixpkgs}:
    let
      system = "x86_64-linux";
      fletSrc = builtins.fetchTarball {
        url = "https://github.com/flet-dev/flet/archive/refs/tags/v0.80.5.tar.gz";
        sha256 = "1hj48zhs4fp57l9k4903wkffa7d24sr0hc3j97p1l1f8q50z1xf0";
      };
      pkgs = import nixpkgs {
        inherit system;
        # overlay to fix flet issue:
        # > pkgs.buildEnv error: two given paths contain a conflicting subpath:
        # >   `/nix/store/5rgpiz9ld6cz0wdxp9vxlhaxr8m2pbpk-python3.13-flet-cli-0.28.3/bin/flet' and
        # >   `/nix/store/mzz9p08454rfhvi9z6mv0nwax0l8ixn4-python3.13-flet-0.28.3/bin/flet'
        # > hint: this may be caused by two different versions of the same package in buildEnv's `paths` parameter
        overlays = [
          (final: prev: {
            python313 = prev.python313.override {
              packageOverrides = pfinal: pprev: {
                flet = pprev.flet.overrideAttrs (old: {
                  version = "0.80.5";
                  src = fletSrc;
                  sourceRoot = "source/sdk/python/packages/flet";
                  nativeBuildInputs = (old.nativeBuildInputs or []) ++ [ pfinal.setuptools pfinal.wheel pfinal.setuptools-scm ];
                  propagatedBuildInputs = (old.propagatedBuildInputs or []) ++ [ pfinal.msgpack ];
                  doCheck = false;
                  checkPhase = "true";
                  # Force pytest to be skipped
                  pytestCheckPhase = "true";
                  nativeCheckInputs = [];
                  checkInputs = [];
                  postFixup = (old.postFixup or "") + ''
                    if [ -f $out/bin/flet ]; then
                      mv $out/bin/flet $out/bin/flet-server
                    fi
                    export version_file=$(find $out -name version.py)
                    echo "version = '0.80.5'" > $version_file
                    echo "flet_version = '0.80.5'" >> $version_file
                    echo "flutter_version = '3.38.7'" >> $version_file
                    echo "pyodide_version = '0.27.0'" >> $version_file
                  '';
                });
                flet-desktop = pprev.flet-desktop.overrideAttrs (old: {
                  version = "0.80.5";
                  src = fletSrc;
                  sourceRoot = "source/sdk/python/packages/flet-desktop";
                  nativeBuildInputs = (old.nativeBuildInputs or []) ++ [ pfinal.setuptools pfinal.wheel pfinal.setuptools-scm ];
                  propagatedBuildInputs = (old.propagatedBuildInputs or []) ++ [ pfinal.setuptools ];
                  doCheck = false;
                  checkPhase = "true";
                  pytestCheckPhase = "true";
                  nativeCheckInputs = [];
                  checkInputs = [];
                  postFixup = (old.postFixup or "") + ''
                    export version_file=$(find $out -name version.py)
                    if [ -n "$version_file" ]; then
                      echo "version = '0.80.5'" > $version_file
                      echo "flet_version = '0.80.5'" >> $version_file
                      echo "flutter_version = '3.38.7'" >> $version_file
                      echo "pyodide_version = '0.27.0'" >> $version_file
                    fi
                  '';
                });
                flet-web = pprev.flet-web.overrideAttrs (old: {
                  version = "0.80.5";
                  src = fletSrc;
                  sourceRoot = "source/sdk/python/packages/flet-web";
                  nativeBuildInputs = (old.nativeBuildInputs or []) ++ [ pfinal.setuptools pfinal.wheel pfinal.setuptools-scm ];
                  propagatedBuildInputs = (old.propagatedBuildInputs or []) ++ [ pfinal.setuptools ];
                  doCheck = false;
                  checkPhase = "true";
                  pytestCheckPhase = "true";
                  nativeCheckInputs = [];
                  checkInputs = [];
                  postFixup = (old.postFixup or "") + ''
                    export version_file=$(find $out -name version.py)
                    if [ -n "$version_file" ]; then
                      echo "version = '0.80.5'" > $version_file
                      echo "flet_version = '0.80.5'" >> $version_file
                      echo "flutter_version = '3.38.7'" >> $version_file
                      echo "pyodide_version = '0.27.0'" >> $version_file
                    fi
                  '';
                });
                flet-cli = pprev.flet-cli.overrideAttrs (old: {
                  version = "0.80.5";
                  src = fletSrc;
                  sourceRoot = "source/sdk/python/packages/flet-cli";
                  nativeBuildInputs = (old.nativeBuildInputs or []) ++ [ pfinal.setuptools pfinal.wheel pfinal.setuptools-scm ];
                  propagatedBuildInputs = (old.propagatedBuildInputs or []) ++ [ pfinal.setuptools ];
                  doCheck = false;
                  checkPhase = "true";
                  pytestCheckPhase = "true";
                  nativeCheckInputs = [];
                  checkInputs = [];
                  postInstall = ''
                    mkdir -p $out/bin
                    makeWrapper ${pfinal.flet}/bin/flet-server $out/bin/flet \
                      --prefix PYTHONPATH : $PYTHONPATH
                  '';
                  postFixup = (old.postFixup or "") + ''
                    export version_file=$(find $out -name version.py)
                    if [ -n "$version_file" ]; then
                      echo "version = '0.80.5'" > $version_file
                      echo "flet_version = '0.80.5'" >> $version_file
                      echo "flutter_version = '3.38.7'" >> $version_file
                      echo "pyodide_version = '0.27.0'" >> $version_file
                    fi
                  '';
                });
              };
            };
          })
        ];
      };
      pythonEnv = pkgs.python313.withPackages (ps: [
        ps.aiohttp
        # ps.httpx
        ps.flet
        ps.flet-cli
        ps.pip
        # ps.msgpack
      ]);
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          direnv
          pythonEnv
          # zenity
        ];
        shellHook = ''
          echo "Welcome to the devShell!" | ${pkgs.lolcat}/bin/lolcat
          echo "Run 'echo \"use flake\" > .envrc' to enable direnv" | ${pkgs.lolcat}/bin/lolcat
          echo "Use 'direnv allow' to automatically load this environment" | ${pkgs.lolcat}/bin/lolcat
        '';
      };
    };
}