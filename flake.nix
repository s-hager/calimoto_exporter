# https://wiki.nixos.org/wiki/Android
# NixOS uses the androidenv package for building android SDKs and manually creating emulators without the use of Android Studio. Example android sdk is androidenv.androidPkgs.androidsdk. They also include all of the SDK tools such as sdkmanager and avdmanager needed to create emulators.
# Note: androidenv.androidPkgs_9_0 has been replaced with androidenv.androidPkgs in nixos 24.11, see backward-incompatibilities-sec-release-2411-incompatibilities, so all the androidPkgs references below will be androidPkgs_9_0 if you are still using 24.05 or below.

# The first link provides a guide for creating a custom android SDK, using a predefined SDK, and how to nixify an emulator. The second link is an extra guide that might have some helpful tips for improving your workflow.

#     Official Android SDK guide from NixOS.org https://nixos.org/manual/nixpkgs/unstable/#android
#     Reproducing Android app deployments https://sandervanderburg.blogspot.de/2014/02/reproducing-android-app-deployments-or.html

# When creating emulators with Nix's emulateApp function as mentioned in the first link, your IDE should now be able to recognize the emulator but you won't be able to run the code.
# To run it, view the first link on how to run the apk file in the emulator.

# To run emulateApp, build it with nix-build fileName.nix.
# It'll build in the folder result.
# run it with ./result/bin/run-test-emulator 

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
        config = {
          android_sdk.accept_license = true;
          allowUnfree = true;
        };

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
                flet-secure-storage = pprev.buildPythonPackage rec {
                  pname = "flet-secure-storage";
                  version = "0.80.5";
                  pyproject = true;
                  src = pkgs.fetchurl {
                    url = "https://files.pythonhosted.org/packages/10/d8/87cb3bc3014dd33fece945e6dd6db491e7544b968020abe7501a1f3d5a71/flet_secure_storage-0.80.5.tar.gz";
                    sha256 = "bd92a12c974a6e875b74b79b448780143bb27f94c81ab8cae5da0ad3d4740f5a";
                  };
                  nativeBuildInputs = [ pfinal.setuptools pfinal.wheel pfinal.poetry-core ];
                  dependencies = [ pfinal.flet ];
                  
                  pythonRemoveDeps = [ "flet" ];
                  
                  postPatch = ''
                    sed -i -e 's/flet = "0.80.5"/flet = "*"/g' pyproject.toml || true
                    sed -i -e 's/flet==0.80.5/flet/g' pyproject.toml || true
                  '';
                  
                  doCheck = false;
                };
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
        ps.flet-secure-storage
        ps.pip
        # ps.msgpack
      ]);
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        packages = [ 
          # run with: run-test-emulator
          (pkgs.androidenv.emulateApp {
            name = "emulate-MyAndroidApp";
            platformVersion = "36";
            abiVersion = "x86_64"; # armeabi-v7a, mips, x86_64
            systemImageType = "google_apis_playstore";
            configOptions = {
              "hw.keyboard" = "yes";
              # Add custom screen dimensions here
              "hw.lcd.width" = "1080";
              "hw.lcd.height" = "1920";
              "hw.lcd.density" = "420";
            };
            # It is also possible to specify an APK to deploy inside the emulator and the package and activity names to launch it:
            # app = "MyApk.apk";
            # package = "com.rovio.angrybirds";
            # activity = "com.rovio.fusion.App";
          })
          pkgs.android-tools
        ];

        buildInputs = with pkgs; [
          direnv
          pythonEnv
          # zenity
        ];
        QT_QPA_PLATFORM = "xcb";
        shellHook = ''
          echo "Welcome to the devShell!" | ${pkgs.lolcat}/bin/lolcat
          echo "Run 'echo \"use flake\" > .envrc' to enable direnv" | ${pkgs.lolcat}/bin/lolcat
          echo "Use 'direnv allow' to automatically load this environment" | ${pkgs.lolcat}/bin/lolcat
        '';
      };
    };
}