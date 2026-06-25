#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_version(value: str) -> tuple[int, int, int]:
	match = VERSION_RE.match(value)
	if not match:
		sys.exit(f"Error: invalid version {value!r} (expected MAJOR.MINOR.PATCH)")
	return tuple(int(part) for part in match.groups())


def get_last_tag() -> str:
	result = subprocess.run(
		["git", "describe", "--abbrev=0", "--tags", "master"],
		capture_output=True,
		text=True,
		check=True,
	)
	return result.stdout.strip()


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Validate release tag is one step ahead of the last git tag",
	)
	parser.add_argument(
		"--major",
		action="store_true",
		help="Allow a major version bump (x.0.0)",
	)
	parser.add_argument("version", help="Release version/tag")
	args = parser.parse_args()

	last_tag = get_last_tag()
	last = parse_version(last_tag)
	new = parse_version(args.version)
	major, minor, patch = last

	if new <= last:
		sys.exit(f"Error: {args.version} must be ahead of last tag {last_tag}")

	if args.major:
		expected = (major + 1, 0, 0)
		if new != expected:
			expected_str = ".".join(str(part) for part in expected)
			sys.exit(f"Error: with --major, expected {expected_str}, got {args.version}")
	else:
		patch_bump = (major, minor, patch + 1)
		minor_bump = (major, minor + 1, 0)
		if new not in {patch_bump, minor_bump}:
			patch_str = ".".join(str(part) for part in patch_bump)
			minor_str = ".".join(str(part) for part in minor_bump)
			sys.exit(
				f"Error: {args.version} must be one step ahead of {last_tag}\n"
				f"  Expected patch bump: {patch_str}\n"
				f"  Expected minor bump: {minor_str}\n"
				f"  Or use --major for a major release",
			)

	print(f"OK: {args.version} is valid next release after {last_tag}")


if __name__ == "__main__":
	main()
