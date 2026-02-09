EXCLUDES := .git,__pycache__,.direnv,build,.credentials,.envrc,.gitignore,flake.lock,flake.nix,Makefile,README.md

.PHONY: run run-web build-web apk debug-apk clean install-deps

# Default target
run:
	flet run frontend.py

run-web:
	flet run --web frontend.py

install-deps:
	mkdir -p __pypackages__ && pip install -r requirements.txt --target __pypackages__ --upgrade

# does not work because of CORS
build-web: install-deps
	flet build web --module-name frontend --exclude $(EXCLUDES)

apk: install-deps
	flet build apk --module-name frontend --exclude $(EXCLUDES)

debug-apk: install-deps
	flet build apk --flutter-build-args="--debug" --module-name frontend --exclude $(EXCLUDES)

clean:
	rm -rf build
