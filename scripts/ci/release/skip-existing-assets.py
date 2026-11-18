#!/usr/bin/env python3
"""
Remove downloaded artifacts that are already attached to the GitHub release,
so the release action does not add (and overwrite) them again.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

YELLOW = "\033[33m"
RESET = "\033[0m"


def get_existing_assets(tag: str) -> set[str] | None:
	result = subprocess.run(
		[
			"gh",
			"release",
			"view",
			tag,
			"--json",
			"assets",
			"--jq",
			".assets[].name",
		],
		capture_output=True,
		text=True,
		check=False,
	)
	if result.returncode != 0:
		return None
	return set(result.stdout.splitlines())


def main() -> int:
	tag = os.environ.get("TAG")
	if not tag:
		print("TAG must be set", file=sys.stderr)
		return 1
	artifacts_dir = Path(os.environ.get("ARTIFACTS_DIR", "artifacts"))

	if not artifacts_dir.is_dir():
		print(f"Artifacts directory '{artifacts_dir}' does not exist; nothing to skip.")
		return 0

	existing = get_existing_assets(tag)
	if existing is None:
		print(f"Release '{tag}' does not exist yet; all artifacts will be uploaded.")
		return 0

	for path in sorted(artifacts_dir.rglob("*")):
		if not path.is_file() or path.name not in existing:
			continue
		print(
			f"{YELLOW}Skipping {path.name}: asset already exists in release {tag}{RESET}"
		)
		path.unlink()

	return 0


if __name__ == "__main__":
	sys.exit(main())
