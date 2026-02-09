# Calimoto Exporter

A tool to export your routes and recorded tracks from [calimoto](https://calimoto.com/) as GPX files.

**Features:**
- **Export Routes & Tracks:** Download both your planned routes and recorded tracks.
- **Rich GPX Data:** Exports include GPS coordinates, elevation, timestamps, and speed (for tracks).
- **Multiple Interfaces:**
  - **GUI:** A user-friendly desktop application (built with Flet).
  - **CLI:** A command-line interface for quick exports.
- **Secure:** Runs entirely locally on your machine. Requests are made directly to Calimoto's servers.

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

### Run CLI
To run the command-line interface for exporting routes/tracks:
```bash
python cli.py
```

### Run Locally (Desktop App)
```bash
make run
```

### Run Web Version (Local Browser)
```bash
make run-web
```

### Build for Web
This will generate the web assets in the `build/web` directory.
> **Note:** Not working due to CORS.
```bash
make build-web
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