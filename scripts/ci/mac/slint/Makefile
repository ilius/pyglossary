.PHONY: all uv venv deps-brew deps-python patch nuitka-build copy-assets dmg

# All actual build logic lives in build.sh; this Makefile is a thin,
# discoverable wrapper around it (mirroring scripts/ci/mac/Makefile),
# kept for local/manual builds. CI calls build.sh directly.

export APPNAME ?= PyGlossarySlint
export DIST_DIR ?= dist.nuitka.slint
export MAIN_SCRIPT ?= main.py
export SLINT_VERSION ?= 1.17.0b2
export PYTHON_VERSION ?= 3.13

all:
	./build.sh all

uv:
	./build.sh uv

venv:
	./build.sh venv

deps-brew:
	./build.sh deps-brew

deps-python:
	./build.sh deps-python

patch:
	./build.sh patch

nuitka-build:
	./build.sh nuitka-build

copy-assets:
	./build.sh copy-assets

dmg:
	./build.sh dmg
