#!/usr/bin/env python3
"""Populate the release-notes GitHub issue and pull request metadata cache."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent.parent
NOTES_SCRIPT = ROOT / "scripts" / "create-release" / "create-release-notes.py"
GITHUB_REFERENCE_URL_RE = re.compile(
	r"https://github\.com/ilius/pyglossary/(?:issues|pull)/(\d+)",
)


def load_release_notes_module() -> ModuleType:
	"""Load the cache helpers shared with the release-notes generator."""
	spec = importlib.util.spec_from_file_location("create_release_notes", NOTES_SCRIPT)
	if spec is None or spec.loader is None:
		raise RuntimeError(f"Could not load {NOTES_SCRIPT}")
	module = importlib.util.module_from_spec(spec)
	sys.modules[spec.name] = module
	spec.loader.exec_module(module)
	return module


def run_git(*args: str) -> str:
	return subprocess.run(
		["git", *args],
		cwd=ROOT,
		capture_output=True,
		text=True,
		check=True,
	).stdout


def referenced_numbers(release_notes: ModuleType) -> set[str]:
	"""Collect #NNN references from all commits and currently tracked files."""
	commit_messages = run_git("log", "--all", "--format=%B")
	release_notes_text = run_git("grep", "-h", "-E", r"#[0-9]+", "--", "doc/releases")
	github_links = run_git(
		"grep",
		"-h",
		"-E",
		r"https://github\.com/ilius/pyglossary/(issues|pull)/[0-9]+",
	)
	return {
		*release_notes.ISSUE_PR_RE.findall(commit_messages),
		*release_notes.ISSUE_PR_RE.findall(release_notes_text),
		*GITHUB_REFERENCE_URL_RE.findall(github_links),
	}


def fetch_issue_pages(
	release_notes: ModuleType,
	numbers: set[str],
	refs: dict[str, object],
) -> int:
	"""Fetch issue pages until all requested numbers have been resolved."""
	missing = numbers - refs.keys()
	page = 1
	fetched = 0
	while missing:
		params = urllib.parse.urlencode({"state": "all", "per_page": 100, "page": page})
		request = urllib.request.Request(
			f"https://api.github.com/repos/{release_notes.REPO}/issues?{params}",
			headers={
				"Accept": "application/vnd.github+json",
				"User-Agent": "pyglossary-release-notes",
			},
		)
		try:
			with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
				items = json.load(response)
		except (
			urllib.error.HTTPError,
			urllib.error.URLError,
			TimeoutError,
			json.JSONDecodeError,
		) as error:
			print(
				f"Error: could not fetch GitHub issue page {page}: {error}",
				file=sys.stderr,
			)
			break
		if not isinstance(items, list):
			print(f"Error: unexpected GitHub response on page {page}", file=sys.stderr)
			break
		for item in items:
			if not isinstance(item, dict):
				continue
			number = str(item.get("number", ""))
			if number not in missing:
				continue
			user = item.get("user")
			author = user.get("login", "") if isinstance(user, dict) else ""
			if not isinstance(author, str):
				continue
			kind = "pull" if item.get("pull_request") else "issue"
			refs[number] = release_notes.GitHubReference(kind, author)
			missing.remove(number)
			fetched += 1
		if len(items) < 100:
			break
		page += 1
	return fetched


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Populate the GitHub issue/PR metadata cache used by release notes.",
	)
	parser.add_argument(
		"--no-network",
		action="store_true",
		help="Report uncached references without contacting GitHub",
	)
	args = parser.parse_args()

	release_notes = load_release_notes_module()
	numbers = referenced_numbers(release_notes)
	cache_path = release_notes.GITHUB_REFS_CACHE
	refs = release_notes.load_github_refs(cache_path)
	missing_before = numbers - refs.keys()
	fetched = 0 if args.no_network else fetch_issue_pages(release_notes, numbers, refs)
	release_notes.save_github_refs(cache_path, refs)
	missing_after = numbers - refs.keys()
	print(f"Found {len(numbers)} GitHub references")
	print(f"Fetched {fetched} references")
	print(f"Cached {len(numbers) - len(missing_after)} references")
	if missing_after:
		print(f"Unresolved: {', '.join(sorted(missing_after, key=int))}", file=sys.stderr)
		if args.no_network or missing_before:
			sys.exit(1)


if __name__ == "__main__":
	main()
