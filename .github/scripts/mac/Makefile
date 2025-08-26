.PHONY: all

APPNAME ?= PyGlossary
DIST_DIR ?= dist-nuitka
MAIN_SCRIPT ?= main.py
ARCH := $(shell uname -m)
MACOS_VERSION := $(shell sw_vers -productVersion)
OS := macos-$(ARCH)-$(MACOS_VERSION)
VERSION := $(shell git describe --abbrev=1)
VERSION_WITH_HASH := $(shell git describe)

export APPNAME DIST_DIR MAIN_SCRIPT

all: uv venv deps-brew deps-python patch nuitka-build copy-assets dmg

uv:
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }

venv:
	cd ../../.. && test -d .venv || uv venv

deps-brew:
	brew install libffi gettext cmake ccache pkg-config icu4c lzo

deps-python:
	cd ../../.. && source .venv/bin/activate && $(CURDIR)/prepare-deps.sh

patch:
	cd ../../.. && python3 $(CURDIR)/patch_sources.py

nuitka-build:
	cd ../../.. && . .venv/bin/activate && $(CURDIR)/nuitka-build.sh

copy-assets:
	cd ../../.. && python3 $(CURDIR)/copy_assets.py

dmg:
	cd ../../.. &&  $(CURDIR)/make-dmg.sh $(APPNAME) $(DIST_DIR) $(OS) $(VERSION) $(VERSION_WITH_HASH)
