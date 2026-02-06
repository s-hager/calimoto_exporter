### PWA Build
- **Command**: `flet build web --module-name app --exclude .direnv,.git`
- **Output**: The PWA has been generated in `build/web`.

## How to Run
To serve the built PWA locally:

```bash
python3 -m http.server --directory build/web
```
Then open `http://localhost:8000` in your browser.





python app.py