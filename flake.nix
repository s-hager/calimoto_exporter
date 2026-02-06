{
  description = "react native flake";

  inputs.nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";

  outputs = { self, nixpkgs}:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
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
        # ps.playwright
        ps.aiohttp
        ps.flet
        # ps.flet-desktop
        ps.flet-cli
      ]);
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          hello
          devenv
          direnv
          pythonEnv
          # pkgs.playwright
          # pkgs.flutter
          # pkgs.jdk17
          # pkgs.flet-client-flutter
        ];
        shellHook = ''
          echo "Welcome to the devShell!" | ${pkgs.lolcat}/bin/lolcat
          echo "Run 'echo \"use flake\" > .envrc' to enable direnv" | ${pkgs.lolcat}/bin/lolcat
          echo "Use 'direnv allow' to automatically load this environment" | ${pkgs.lolcat}/bin/lolcat
          # export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
          # export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
        '';
          # exec zsh -c 'echo "Welcome to the devShell!"'
      };
    };
}