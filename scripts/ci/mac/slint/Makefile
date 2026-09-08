.PHONY: all uv venv deps-brew deps-python patch nuitka-build copy-assets dmg

# All actual build logic lives in build.py; this Makefile is a thin,
# discoverable wrapper around it (mirroring scripts/ci/mac/Makefile),
# kept for local/manual builds. CI calls build.py directly.

export APPNAME ?= PyGlossarySlint
export DIST_DIR ?= dist.nuitka.slint
export MAIN_SCRIPT ?= main.py
export SLINT_VERSION ?= 1.17.0b2
export PYTHON_VERSION ?= 3.13

all:
	./build.py all

uv:
	./build.py uv

venv:
	./build.py venv

deps-brew:
	./build.py deps-brew

deps-python:
	./build.py deps-python

patch:
	./build.py patch

nuitka-build:
	./build.py nuitka-build

copy-assets:
	./build.py copy-assets

dmg:
	./build.py dmg
