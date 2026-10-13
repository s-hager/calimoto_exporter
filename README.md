# Calimoto Exporter

A tool to export your routes and recorded tracks from [calimoto](https://calimoto.com/) as GPX files.

**Features:**
- **Export Routes & Tracks:** Download both your planned routes and recorded tracks.
- **Rich GPX Data:** Exports include GPS coordinates, elevation, timestamps, and speed (for tracks).
- **Multiple Interfaces:**
  - **Web UI:** Fast, responsive multi-user web application with direct browser GPX & ZIP downloads.
  - **GUI:** Desktop application (built with Flet).
  - **CLI:** Command-line interface for quick batch exports.
- **Secure & Multi-User:** Run it locally or self-host on a server. Sessions are isolated in-memory and credentials are never stored on the server disk.

## Setup

This project uses [Nix](https://nixos.org/) for dependency management.

1. Ensure you have Nix installed.
2. Enable [direnv](https://direnv.net/) to automatically load the environment:
   ```bash
   direnv allow
   ```
   Or manually enter the shell:
   ```bash
   nix develop
   ```

## Usage

### Run Web Server (Recommended for Self-Hosting)
```bash
# Using Nix Flakes directly
nix run .

# Or using Make (inside nix develop / direnv)
make run-server
```
Then open `http://localhost:8080` in your browser.

### NixOS Module (Deploy on your NixOS server)
You can directly import this flake in your NixOS configuration:

```nix
# In your flake.nix or configuration.nix:
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    calimoto-exporter.url = "github:s-hager/calimoto_exporter"; # or path:/path/to/calimoto_exporter
  };

  outputs = { self, nixpkgs, calimoto-exporter, ... }: {
    nixosConfigurations.your-server = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        calimoto-exporter.nixosModules.default
        {
          services.calimoto-exporter = {
            enable = true;
            port = 8080;
            openFirewall = true; # opens port 8080 in firewall
          };
        }
      ];
    };
  };
}
```

### Run CLI
To run the command-line interface for exporting routes/tracks:
```bash
python cli.py
```

### Run Locally (Desktop App)
```bash
make run
```

### Build APK (Android)
To build an Android APK:
```bash
make apk
```

### Build Debug APK (Android)
To build a debug Android APK:
```bash
make debug-apk
```

### Clean Build Directory
```bash
make clean
```

## Configuration

For testing, you can provide your Calimoto credentials in a `.credentials` file in the root directory (JSON format) or via environment variables.
In the release app, the credentials are entered via a login form.

### .credentials file
```json
{
  "email": "your-email@example.com",
  "password": "your-password"
}
```

### Environment Variables
- `CALIMOTO_USERNAME`
- `CALIMOTO_PASSWORD`