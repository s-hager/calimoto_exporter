.PHONY: run-local run-web build clean install-deps serve

# Default target
run-local:
	flet run frontend.py

run-web:
	flet run --web frontend.py

install-deps:
	mkdir -p __pypackages__ && nix-shell -p python3Packages.pip --run "pip install -r requirements.txt --target __pypackages__ --upgrade"

build: install-deps
	rm -rf build && flet build web --module-name frontend --exclude .direnv,.git,.direnv,.gitignore,.credentials,.envrc,__pycache__,build,flake.nix,flake.lock,README.md

serve:
	python3 -m http.server --directory build/web 8000

clean:
	rm -rf build
