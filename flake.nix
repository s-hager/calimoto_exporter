{
  description = "react native flake";

  inputs.nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";

  outputs = { self, nixpkgs}:
    let
      system = "x86_64-linux";
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
                  postFixup = (old.postFixup or "") + ''
                    if [ -f $out/bin/flet ]; then
                      mv $out/bin/flet $out/bin/flet-server
                    fi
                  '';
                });
                flet-cli = pprev.flet-cli.overrideAttrs (old: {
                  postInstall = ''
                    mkdir -p $out/bin
                    makeWrapper ${pfinal.flet}/bin/flet-server $out/bin/flet \
                      --prefix PYTHONPATH : $PYTHONPATH
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
      ]);
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          hello
          devenv
          direnv
          pythonEnv
        ];
        shellHook = ''
          echo "Welcome to the devShell!" | ${pkgs.lolcat}/bin/lolcat
          echo "Run 'echo \"use flake\" > .envrc' to enable direnv" | ${pkgs.lolcat}/bin/lolcat
          echo "Use 'direnv allow' to automatically load this environment" | ${pkgs.lolcat}/bin/lolcat
        '';
      };
    };
}