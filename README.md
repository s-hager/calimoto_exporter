# Calimoto Exporter

A tool to export your routes and tracks from Calimoto as GPX files.

## Setup

This project uses [Nix](https://nixos.org/) for dependency management.

1.  Ensure you have Nix installed.
2.  Enable [direnv](https://direnv.net/) to automatically load the environment:
    ```bash
    direnv allow
    ```
    Or manually enter the shell:
    ```bash
    nix develop
    ```

## Usage

A `Makefile` is provided for common tasks.

### Run Locally (Desktop App)
```bash
make run-local
```

### Run Web Version (Local Browser)
```bash
make run-web
```

### Build for Web
This will generate the web assets in the `build/web` directory.
```bash
make build
```

### Serve Web Build
To serve the built web application locally:
```bash
make serve
```

## Configuration

For testing, you can provide your Calimoto credentials in a `.credentials` file in the root directory (JSON format) or via environment variables.

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