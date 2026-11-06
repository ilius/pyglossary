.PHONY: all uv venv deps-brew deps-python patch unpatch nuitka-build copy-assets dmg

# All actual build logic lives in build.py; this Makefile is a thin,
# discoverable wrapper around it (mirroring scripts/ci/mac/Makefile),
# kept for local/manual builds. CI calls build.py directly.

export APPNAME ?= PyGlossarySlint
export DIST_DIR ?= dist.nuitka.slint
export MAIN_SCRIPT ?= main.py
export SLINT_VERSION ?= 1.18.1b1
export PYTHON_VERSION ?= 3.13

# `patch` edits tracked files for the nuitka build; restore them afterwards
# (even on failure, keeping the build's exit status) so local builds leave the
# working tree clean. NOTE: discards any local edits to these two files.
PATCHED := pyglossary/ui/argparse_main.py __init__.py
UNPATCH := git -C "$$(git rev-parse --show-toplevel)" checkout -- $(PATCHED)

all:
	./build.py all; status=$$?; $(UNPATCH); exit $$status

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

unpatch:
	$(UNPATCH)

nuitka-build:
	./build.py nuitka-build; status=$$?; $(UNPATCH); exit $$status

copy-assets:
	./build.py copy-assets

dmg:
	./build.py dmg
