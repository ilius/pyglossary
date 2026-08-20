#!/usr/bin/env python3
"""Generate doc/releases/VERSION.md from git history."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from os.path import join, splitext
from pathlib import Path

REPO = "ilius/pyglossary"
GITHUB = f"https://github.com/{REPO}"
ROOT = Path(__file__).resolve().parent.parent.parent
PLUGINS_META = ROOT / "plugins-meta" / "index.json"
RELEASES_DIR = ROOT / "doc" / "releases"
GITHUB_REFS_CACHE = ROOT / "scripts" / "create-release" / "github-refs.csv"
LEGACY_GITHUB_REFS_CACHE = GITHUB_REFS_CACHE.with_suffix(".json")

SKIP_SUBJECT_RE = re.compile(
	r"^(version \d|add doc/releases/|update doc/releases/|ignore ruff|"
	r"fix ruff|fix mypy|remove unused type ignore)",
	re.IGNORECASE,
)
MAINTENANCE_SUBJECT_RE = re.compile(
	r"\b(?:refactor(?:ing)?|reformat|minor cleanup|e2e test|fix ruff)\b|"
	r"^change issue refs to urls$|^change config param\b|^remove unused\b|"
	r"^update scripts/create-release/|\bvalid__all__\b",
	re.IGNORECASE,
)
ISSUE_PR_RE = re.compile(r"(?<![`\w])#(\d+)(?![`\w])")
PARENTHESIZED_ISSUE_PR_RE = re.compile(r"\s*\(#(\d+)\)")
REPEATED_PR_AUTHOR_RE = re.compile(
	r"(?P<prefix>PR\s+\[#\d+\]\([^)]*\)(?:,\s+\[#\d+\]\([^)]*\))*)"
	r"\s+by\s+(?P<author>\[@[^]]+\]\([^)]*\)),\s+PR\s+"
	r"(?P<number>\[#\d+\]\([^)]*\))\s+by\s+(?P=author)",
)
VERSION_COMMIT_RE = re.compile(r"^version \d", re.IGNORECASE)
SECURITY_RE = re.compile(
	r"security|malicious|path traversal|absolute path|\.\./|refuse absolute",
	re.IGNORECASE,
)
COMPAT_RE = re.compile(
	r"python_requires|require python|breaking|compat|default (?:gui|is now)|"
	r"no longer|deprecated|switch to python\s+\d|drop python\s+\d",
	re.IGNORECASE,
)
COMPAT_PRESERVE_RE = re.compile(
	r"for compatibility|keep(?:ing)? compatibility|compatibility is maintained|"
	r"backward.compatible|make compatible|compatible with|compat with|"
	r"-compatible\b",
	re.IGNORECASE,
)
FIX_RE = re.compile(r"\bfix\b|\bbugfix\b|bug fix|regression", re.IGNORECASE)
NEW_FORMAT_RE = re.compile(
	r"\badd\b.*\b(reader|writer|plugin)\b|\bnew (reader|writer|format)\b|"
	r"\bread/write format\b",
	re.IGNORECASE,
)
CLI_RE = re.compile(
	r"^add --|^--[\w-]+|view-glossary|diff-glossary|pyglossary-view|"
	r"pyglossary-diff|argparse|help message|help text",
	re.IGNORECASE,
)
UI_LAUNCHER_FLAG_RE = re.compile(r"^--(?:ui|tkw|qt6|qt|gtk4|gtk3|gtk)\b", re.IGNORECASE)
UI_RE = re.compile(
	r"\bui[_:]|^ui_gtk|^ui_tk|^ui_qt|gtk|tkinter|tk wizard|qt6|about dialog|"
	r"drag-and-drop|wizard",
	re.IGNORECASE,
)
IMPROVE_RE = re.compile(r"\bsupport\b|\bimprove\b|\benhance\b|\bricher\b", re.IGNORECASE)
OTHER_RE = re.compile(
	r"\brefactor\b|\blint|\bci:|github actions|workflow|readme|doc/p/|"
	r"\.cursor/|classifier|pyproject|mypy|ruff|pylint|typing|"
	r"scripts/gen|contributing|architecture",
	re.IGNORECASE,
)

PLUGIN_PATH_RE = re.compile(r"pyglossary/plugins/([^/]+)/")

UI_PATH_RE = re.compile(r"pyglossary/ui/")
CORE_PATHS = (
	"pyglossary/glossary",
	"pyglossary/plugin_handler",
	"pyglossary/entry",
	"pyglossary/core.py",
	"pyglossary/option.py",
	"pyglossary/text_utils.py",
	"pyglossary/sort_keys.py",
	"pyglossary/compression.py",
	"pyglossary/flags.py",
	"pyglossary/os_utils.py",
	"pyglossary/reverse.py",
	"pyglossary/xdxf/",
	"pyglossary/html_utils.py",
	"pyglossary/io_utils.py",
)
CLI_TOOL_PATHS = (
	"pyglossary/ui/argparse",
	"pyglossary/ui/main.py",
	"scripts/view-glossary",
	"scripts/diff-glossary",
	"pyglossary-view",
	"pyglossary-diff",
	"view-glossary",
	"diff-glossary",
)
META_PATHS = (
	".github/",
	".cursor/",
	"scripts/gen",
	"scripts/create-release",
	"pyproject.toml",
	"setup.py",
	"setup.cfg",
	".pre-commit",
	".gitignore",
	".editorconfig",
	"tox.ini",
	"Makefile",
	"LICENSE",
	"CONTRIBUTING",
)


@dataclass
class FileSignals:
	"""Aggregate signals from a commit's modified file paths."""

	ui_files: bool = False
	plugin_files: bool = False
	core_files: bool = False
	cli_files: bool = False
	meta_files: bool = False
	test_files: bool = False
	doc_files: bool = False
	plugin_modules: set[str] = field(default_factory=set)

	@classmethod
	def from_files(cls, files: list[str]) -> FileSignals:
		sig = cls()
		for raw in files:
			f = raw.replace("\\", "/")
			m = PLUGIN_PATH_RE.search(f)
			if m and m.group(1) != "formats_common":
				sig.plugin_files = True
				sig.plugin_modules.add(m.group(1))
				continue
			if UI_PATH_RE.search(f):
				sig.ui_files = True
				continue
			if any(f.startswith(p) or f"/{p}" in f for p in CLI_TOOL_PATHS):
				sig.cli_files = True
				continue
			if any(f.startswith(p) or f"/{p}" in f for p in CORE_PATHS):
				sig.core_files = True
				continue
			if any(f.startswith(p) for p in META_PATHS):
				sig.meta_files = True
				continue
			if "/tests/" in f or f.endswith("_test.py") or f.startswith("tests/"):
				sig.test_files = True
				continue
			if f.startswith("doc/") or f.endswith(".md"):
				sig.doc_files = True
				continue
		return sig


@dataclass
class PluginMeta:
	module: str
	lname: str
	name: str
	description: str
	can_read: bool
	can_write: bool
	wiki_title: str = ""
	wiki_url: str = ""


@dataclass
class Commit:
	hash: str
	subject: str
	author_name: str
	author_email: str
	files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GitHubReference:
	"""Cached metadata for an issue or pull request mentioned by a commit."""

	kind: str
	author: str = ""


@dataclass
class NoteEntry:
	section: str
	subsection: str | None
	text: str
	sort_key: str = ""


SECTIONS: list[tuple[str, str | None]] = [
	("compatibility", None),
	("bug_security", None),
	("bug_core", None),
	("bug_plugins", None),
	("bug_ui", None),
	("feature_formats", "New read/write format functionalities"),
	("feature_cli", "New command-line features"),
	("feature_ui", "New user interface features"),
	("improvements", None),
	("other", None),
	("contributors", None),
]

SECTION_HEADINGS = {
	"compatibility": "### Compatibility changes",
	"bug_security": "### Bug fixes (security)",
	"bug_core": "### Bug fixes (core)",
	"bug_plugins": "### Bug fixes (plugins)",
	"bug_ui": "### Bug fixes (user interface)",
	"features": "### Features",
	"improvements": "### Improvements",
	"other": "### Other changes",
	"contributors": "## New Contributors",
}


def run_git(*args: str) -> str:
	result = subprocess.run(
		["git", *args],
		cwd=ROOT,
		capture_output=True,
		text=True,
		check=True,
	)
	return result.stdout


def git_ref_exists(ref: str) -> bool:
	result = subprocess.run(
		["git", "rev-parse", "--verify", ref],
		cwd=ROOT,
		capture_output=True,
		text=True,
		check=True,
	)
	return result.returncode == 0


def resolve_prev_tag(version: str, prev_tag: str | None) -> str:
	if prev_tag:
		return prev_tag
	if git_ref_exists(f"{version}^"):
		return run_git("describe", "--abbrev=0", "--tags", f"{version}^").strip()
	tags = [
		t.strip() for t in run_git("tag", "--sort=-v:refname").splitlines() if t.strip()
	]
	for tag in tags:
		if tag != version:
			return tag
	sys.exit("Error: could not determine previous tag; pass --prev-tag")


def resolve_end_ref(version: str) -> str:
	if git_ref_exists(version):
		return version
	return "HEAD"


def load_plugins_meta() -> dict[str, PluginMeta]:
	by_module: dict[str, PluginMeta] = {}
	by_lname: dict[str, PluginMeta] = {}
	with PLUGINS_META.open(encoding="utf-8") as file:
		data = json.load(file)
	for item in data:
		meta = PluginMeta(
			module=item["module"],
			lname=item["lname"],
			name=item["name"],
			description=item["description"],
			can_read=item.get("canRead", False),
			can_write=item.get("canWrite", False),
		)
		doc_path = ROOT / "doc" / "p" / f"{meta.lname}.md"
		if doc_path.is_file():
			wiki_match = re.search(
				r"\| Wiki \| \[(.+?)\]\((.+?)\)",
				doc_path.read_text(encoding="utf-8"),
			)
			if wiki_match:
				meta.wiki_title, meta.wiki_url = wiki_match.groups()
		by_module[meta.module] = meta
		by_lname[meta.lname] = meta
	return {"module": by_module, "lname": by_lname}


def plugins_at_ref(ref: str) -> set[str]:
	try:
		output = run_git("ls-tree", "-d", "--name-only", f"{ref}:pyglossary/plugins")
	except subprocess.CalledProcessError:
		return set()
	return {
		line.strip() for line in output.splitlines() if line.strip() != "formats_common"
	}


def collect_commits(prev_tag: str, end_ref: str) -> list[Commit]:
	raw = run_git(
		"log",
		f"{prev_tag}..{end_ref}",
		"--no-merges",
		"--format=%H%x1f%an%x1f%ae%x1f%s",
	)
	commits: list[Commit] = []
	for line in raw.splitlines():
		if not line.strip():
			continue
		hash_, author_name, author_email, subject = line.split("\x1f", 3)
		if VERSION_COMMIT_RE.match(subject.strip()):
			continue
		files = [
			f.strip()
			for f in run_git(
				"diff-tree", "--no-commit-id", "--name-only", "-r", hash_
			).splitlines()
			if f.strip()
		]
		commits.append(
			Commit(
				hash=hash_,
				subject=subject.strip(),
				author_name=author_name,
				author_email=author_email,
				files=files,
			),
		)
	return commits


def plugin_modules_in_files(files: list[str]) -> set[str]:
	modules: set[str] = set()
	for path in files:
		match = PLUGIN_PATH_RE.search(path.replace("\\", "/"))
		if match and match.group(1) != "formats_common":
			modules.add(match.group(1))
	return modules


def load_github_refs(cache_path: Path) -> dict[str, GitHubReference]:
	"""Load previously resolved issue and pull request metadata."""
	if not cache_path.is_file() and LEGACY_GITHUB_REFS_CACHE.is_file():
		return load_legacy_github_refs(LEGACY_GITHUB_REFS_CACHE)
	if not cache_path.is_file():
		return {}
	try:
		with cache_path.open(encoding="utf-8", newline="") as file:
			rows = list(csv.DictReader(file))
	except (OSError, csv.Error) as error:
		print(f"Warning: could not read GitHub reference cache: {error}", file=sys.stderr)
		return {}
	refs: dict[str, GitHubReference] = {}
	for row in rows:
		number = row.get("id")
		kind = row.get("kind")
		author = row.get("author", "")
		if (
			isinstance(number, str)
			and kind in {"issue", "pull"}
			and isinstance(author, str)
		):
			refs[number] = GitHubReference(kind, author)
	return refs


def load_legacy_github_refs(cache_path: Path) -> dict[str, GitHubReference]:
	"""Read the former JSON cache once so it can be migrated to CSV."""
	try:
		data = json.loads(cache_path.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError) as error:
		print(
			f"Warning: could not read legacy GitHub reference cache: {error}",
			file=sys.stderr,
		)
		return {}
	if not isinstance(data, dict):
		return {}
	refs: dict[str, GitHubReference] = {}
	for number, item in data.items():
		if not isinstance(number, str) or not isinstance(item, dict):
			continue
		kind = item.get("kind")
		author = item.get("author", "")
		if kind in {"issue", "pull"} and isinstance(author, str):
			refs[number] = GitHubReference(kind, author)
	return refs


def save_github_refs(cache_path: Path, refs: dict[str, GitHubReference]) -> None:
	"""Persist fetched metadata for future release-note runs."""
	cache_path.parent.mkdir(parents=True, exist_ok=True)
	with cache_path.open("w", encoding="utf-8", newline="") as file:
		writer = csv.writer(file, lineterminator="\n")
		writer.writerow(("id", "kind", "author"))
		for number, ref in sorted(refs.items(), key=lambda item: int(item[0])):
			writer.writerow((number, ref.kind, ref.author))


class GitHubRefResolver:
	"""Resolve GitHub issue references, using a local cache to limit API calls."""

	def __init__(self, cache_path: Path, *, fetch: bool) -> None:
		self.cache_path = cache_path
		self.refs = load_github_refs(cache_path)
		self.fetch = fetch
		self.changed = False

	def resolve(self, number: str) -> GitHubReference | None:
		if number in self.refs:
			return self.refs[number]
		if not self.fetch:
			return None
		url = f"https://api.github.com/repos/{REPO}/issues/{number}"
		request = urllib.request.Request(
			url,
			headers={
				"Accept": "application/vnd.github+json",
				"User-Agent": "pyglossary-release-notes",
			},
		)
		try:
			with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
				data = json.load(response)
		except (
			urllib.error.URLError,
			urllib.error.HTTPError,
			TimeoutError,
			json.JSONDecodeError,
		) as error:
			print(
				f"Warning: could not resolve GitHub #{number}: {error}", file=sys.stderr
			)
			return None
		if not isinstance(data, dict):
			return None
		kind = "pull" if data.get("pull_request") else "issue"
		user = data.get("user")
		author = user.get("login", "") if isinstance(user, dict) else ""
		if not isinstance(author, str):
			return None
		ref = GitHubReference(kind, author)
		self.refs[number] = ref
		self.changed = True
		return ref

	def resolve_all(self, numbers: set[str]) -> dict[str, GitHubReference]:
		for number in sorted(numbers, key=int):
			self.resolve(number)
		if self.changed or self.cache_path.is_file():
			save_github_refs(self.cache_path, self.refs)
		return self.refs


def github_reference_link(
	number: str,
	refs: dict[str, GitHubReference],
	*,
	include_author: bool = True,
) -> str:
	"""Render a cached reference, distinguishing issues from pull requests."""
	ref = refs.get(number)
	if ref is None:
		return f"[#{number}]({GITHUB}/issues/{number})"
	if ref.kind == "issue":
		return f"[#{number}]({GITHUB}/issues/{number})"
	author = (
		f" by [@{ref.author}](https://github.com/{ref.author})"
		if include_author and ref.author
		else ""
	)
	return f"PR [#{number}]({GITHUB}/pull/{number}){author}"


def collapse_repeated_pr_authors(text: str) -> str:
	"""Combine consecutive PRs from one author into one attribution."""
	while match := REPEATED_PR_AUTHOR_RE.search(text):
		replacement = (
			f"{match.group('prefix')}, {match.group('number')} by {match.group('author')}"
		)
		text = text[: match.start()] + replacement + text[match.end() :]
	return text


def link_issues_and_prs(text: str, refs: dict[str, GitHubReference]) -> str:
	def repl(match: re.Match[str]) -> str:
		number = match.group(1)
		link = github_reference_link(number, refs)
		# Avoid "PR PR #123" when the commit already labels the number as a PR.
		if refs.get(number, GitHubReference("issue")).kind == "pull" and re.search(
			rf"\b(?:PR|pull request)\s*#{number}\b", text, re.IGNORECASE
		):
			return link.removeprefix("PR ")
		return link

	return collapse_repeated_pr_authors(ISSUE_PR_RE.sub(repl, text))


def plugin_doc_link(meta: PluginMeta) -> str:
	return (
		f"[{meta.description.split('(')[0].strip() or meta.name}](/doc/p/{meta.lname}.md)"
	)


def plugin_role(meta: PluginMeta) -> str:
	if meta.can_read and meta.can_write:
		return "reader/writer"
	if meta.can_read:
		return "reader"
	if meta.can_write:
		return "writer"
	return "plugin"


def format_new_plugin_bullet(meta: PluginMeta, _subject: str, issue_links: str) -> str:
	role = plugin_role(meta)
	wiki_part = ""
	if meta.wiki_title and meta.wiki_url:
		wiki_part = f"[{meta.wiki_title}]({meta.wiki_url}) "
	desc = meta.description
	if wiki_part and wiki_part not in desc:
		desc = (
			f"{wiki_part}({desc.split('(', 1)[-1]}"
			if "(" in desc
			else f"{wiki_part}{desc}"
		)
	link = f"**{plugin_doc_link(meta)}**"
	suffix = f", {issue_links}" if issue_links else ""
	return f"- {link} {role}{suffix} — {desc.rstrip('.')}"


# Relative paths starting with a known top-level directory
PATH_IN_SUBJECT_RE = re.compile(
	r"(?<![`\w/])"
	r"("
	r"(?:pyglossary|doc|scripts|tests|\.github|\.cursor)"
	r"(?:/[\w._-]+)*"
	r"/?"
	r")"
	r"(?![`\w])",
)
# Bare filenames with a code-like extension (e.g. glossary.py, setup.cfg)
BARE_FILENAME_RE = re.compile(
	r"(?<![`\w/.-])"
	r"([\w][\w._-]*\.(?:py|pyw|cfg|toml|json|yaml|yml|md|txt|sh|bat))"
	r"(?![`\w/])",
)
# Underscore identifiers (e.g. glossary_v2, valid__all__, plugin_prop)
UNDERSCORE_IDENT_RE = re.compile(
	r"(?<![`\w/.])"
	r"(_*[a-zA-Z](?=\w*_\w)\w+)"
	r"(?![`\w/.])",
)
# camelCase or PascalCase identifiers (e.g. relatedFormats, StoreConstAction)
CAMEL_CASE_RE = re.compile(
	r"(?<![`\w/.])"
	r"([a-zA-Z][a-z]+(?:[A-Z][a-z]*)+\w*)"
	r"(?![`\w/.])",
)


def _backtick_path(match: re.Match[str]) -> str:
	p = match.group(1).rstrip("/")
	return f"`{p}`"


# Common English words that should NOT be backtick-wrapped even though
# they match camelCase or underscore patterns.
_PASSTHROUGH_WORDS = frozenset(
	{
		"PyGlossary",
		"GitHub",
		"StarDict",
		"JavaScript",
		"TypeScript",
		"DataFrame",
		"LibreOffice",
		"WordNet",
		"FreeDict",
	}
)


def _file_stems(files: list[str]) -> set[str]:
	"""Collect basenames without extension from modified file paths."""
	stems: set[str] = set()
	for pathStr in files:
		path_ = Path(pathStr)
		stems.add(pathStr)
		stems.add(splitext(path_.name)[0])
		parts = pathStr.split(os.sep)
		for i in range(len(parts)):
			for j in range(i + 1, len(parts) + 1):
				# print(join(*parts[i:j]))
				stems.add(join(*parts[i:j]))
	return stems


def normalize_subject(
	subject: str,
	files: list[str] | None = None,
	refs: dict[str, GitHubReference] | None = None,
) -> str:
	text = subject.strip()
	text = re.sub(r"^[a-f0-9]{8}\s+", "", text)
	# Format trailing commit references as part of the sentence rather than a
	# parenthetical aside, e.g. "Fix parsing (#123)" → "Fix parsing, #123".
	text = PARENTHESIZED_ISSUE_PR_RE.sub(r", #\1", text)
	text = re.sub(r"\bbugfix\b", "bug fix", text, flags=re.IGNORECASE)
	text = re.sub(r"\bBug Fix\b", "Bug fix", text)
	text = re.sub(r"\b[Uu][Ii]\b(?=[\s:])", "UI", text)
	text = re.sub(r"^UI:\s*", "", text)
	text = re.sub(r"\bfeat:\s", "Feature: ", text)
	text = PATH_IN_SUBJECT_RE.sub(_backtick_path, text)
	text = BARE_FILENAME_RE.sub(_backtick_path, text)

	if files:
		stems = _file_stems(files)
		# print(stems)

		def _backtick_stem(match: re.Match[str]) -> str:
			word = match.group(1)
			if match.string[: match.start()].count("`") % 2:
				return word
			if word in _PASSTHROUGH_WORDS:
				return word
			if word in stems:
				# print(f"++ {word} from file path")
				return f"`{word}`"
			return word

		text = re.sub(
			r"(?<!`)(\b[\w][\w/-]*\b)(?!`)",
			_backtick_stem,
			text,
		)

	def _backtick_ident(match: re.Match[str]) -> str:
		name = match.group(1)
		if match.string[: match.start()].count("`") % 2:
			return name
		if name in _PASSTHROUGH_WORDS:
			return name
		# print(f"---------- {name}")
		return f"`{name}`"

	text = UNDERSCORE_IDENT_RE.sub(_backtick_ident, text)
	text = CAMEL_CASE_RE.sub(_backtick_ident, text)

	if (
		text
		and text[0].islower()
		and not re.match(
			r"[\w]+[_./:]+",
			text,
		)
	):
		text = text[0].upper() + text[1:]

	return link_issues_and_prs(text, refs or {})


def is_skip_commit(commit: Commit) -> bool:
	if SKIP_SUBJECT_RE.match(commit.subject):
		return True
	# Exclude implementation-only maintenance, including module-prefixed lint
	# commits such as "kobo: fix ruff errors".
	if MAINTENANCE_SUBJECT_RE.search(commit.subject):
		return True
	return bool(
		commit.files
		and all(
			f.startswith(("doc/releases/", ".cursor/", ".github/workflows/"))
			or f == "doc/releases"
			for f in commit.files
		)
	)


def is_doc_only_commit(files: list[str]) -> bool:
	if not files:
		return False
	return all(
		f.replace("\\", "/").startswith(("doc/", "doc/p/")) or f.endswith(".md")
		for f in files
	)


def is_doc_or_meta_commit(files: list[str], subject: str) -> bool:
	if not files:
		return False
	if is_doc_only_commit(files):
		return True
	return bool(
		subject.lower().startswith(("fix seperator", "do not add table padding"))
		and all(
			"doc/p/" in f.replace("\\", "/") or f.startswith("scripts/gen") for f in files
		)
	)


def categorize_commit(  # noqa: C901, PLR0912, PLR0911
	commit: Commit,
	plugins_before: set[str],
	_plugins_meta: dict[str, dict[str, PluginMeta]],
) -> tuple[str, str | None]:
	subject = commit.subject
	files = commit.files
	sig = FileSignals.from_files(files)

	modules = sig.plugin_modules | plugin_modules_in_files(files)
	new_modules = modules - plugins_before
	existing_modules = modules & plugins_before

	ui_files = sig.ui_files
	plugin_files = sig.plugin_files or bool(modules)
	core_files = sig.core_files
	cli_files = sig.cli_files

	if is_doc_or_meta_commit(files, subject):
		return "other", None

	# Pure meta/CI/tooling commits detected by file paths
	if (
		sig.meta_files
		and not (plugin_files or ui_files or core_files or cli_files)
		and not (sig.doc_files and not is_doc_only_commit(files))
		and not COMPAT_RE.search(subject)
	):
		return "other", None

	if COMPAT_RE.search(subject) and not COMPAT_PRESERVE_RE.search(subject):
		return "compatibility", None

	# Broad documentation sweeps touch many plugin files but are release-note
	# metadata, not improvements to every affected plugin.
	if re.search(r"\bdocstrings?\b", subject, re.IGNORECASE):
		return "other", None

	if SECURITY_RE.search(subject):
		return "bug_security", None

	if FIX_RE.search(subject):
		if re.search(
			r"config flag|argparse|StoreConstAction|registerConfigOption",
			subject,
			re.IGNORECASE,
		):
			return "bug_core", None
		if plugin_files and existing_modules and not new_modules:
			return "bug_plugins", None
		# File-path-based UI detection (even if subject doesn't mention UI)
		if ui_files or (UI_RE.search(subject) and "ui_cmd" in subject.lower()):
			return "bug_ui", None
		if core_files or cli_files:
			return "bug_core", None
		if plugin_files and new_modules:
			return "feature_formats", "New read/write format functionalities"
		if plugin_files:
			return "bug_plugins", None
		# Fallback: use file paths to pick the best bug-fix bucket
		if ui_files:
			return "bug_ui", None
		return "bug_core", None

	if new_modules and (
		NEW_FORMAT_RE.search(subject) or re.search(r"\badd\b", subject, re.IGNORECASE)
	):
		return "feature_formats", "New read/write format functionalities"

	if UI_LAUNCHER_FLAG_RE.search(subject):
		return "feature_ui", "New user interface features"

	# CLI tool detection: subject OR file-path signals
	if (
		(CLI_RE.search(subject) or cli_files)
		and not UI_RE.search(subject)
		and not ui_files
		and (
			cli_files
			or "view-glossary" in subject
			or "diff-glossary" in subject
			or subject.lower().startswith("add --")
		)
	):
		return "feature_cli", "New command-line features"

	# UI feature detection requires an explicit UI signal in the subject so a
	# broad refactor that merely touches UI files is not presented as a feature.
	if UI_RE.search(subject) and (
		"add" in subject.lower()
		or "support" in subject.lower()
		or "drag-and-drop" in subject.lower()
	):
		return "feature_ui", "New user interface features"

	if IMPROVE_RE.search(subject) and (existing_modules or plugin_files):
		return "improvements", None

	if re.search(r"\bsupport\b", subject, re.IGNORECASE) and existing_modules:
		return "improvements", None

	# File-path-based improvement detection for plugin changes without
	# a subject-line keyword
	if (
		(
			plugin_files
			and existing_modules
			and not new_modules
			and not FIX_RE.search(subject)
		)
		and "add" not in subject.lower()
		and not SECURITY_RE.search(subject)
	):
		return "improvements", None

	if OTHER_RE.search(subject) or not (
		plugin_files or ui_files or core_files or cli_files
	):
		return "other", None

	# Fallback "add" handling, refined with file-path signals
	if "add" in subject.lower():
		if UI_RE.search(subject):
			return "feature_ui", "New user interface features"
		if cli_files or CLI_RE.search(subject):
			return "feature_cli", "New command-line features"
		if new_modules:
			return "feature_formats", "New read/write format functionalities"
		if plugin_files and existing_modules:
			return "improvements", None

	# Last resort: let file paths decide
	if ui_files:
		return "other", None
	if core_files:
		return "other", None

	return "other", None


def commit_to_entries(  # noqa: PLR0913
	commit: Commit,
	section: str,
	subsection: str | None,
	plugins_before: set[str],
	plugins_meta: dict[str, dict[str, PluginMeta]],
	refs: dict[str, GitHubReference],
) -> list[NoteEntry]:
	modules = plugin_modules_in_files(commit.files)
	new_modules = sorted(modules - plugins_before)
	entries: list[NoteEntry] = []

	if section == "feature_formats" and new_modules:
		for module in new_modules:
			meta = plugins_meta["module"].get(module)
			if meta is None:
				continue
			issue_links = collapse_repeated_pr_authors(
				", ".join(
					github_reference_link(number, refs)
					for number in ISSUE_PR_RE.findall(commit.subject)
				),
			)
			entries.append(
				NoteEntry(
					section=section,
					subsection=subsection,
					text=format_new_plugin_bullet(meta, commit.subject, issue_links),
					sort_key=meta.lname,
				),
			)
		if entries:
			return entries

	if section == "bug_plugins" and modules:
		for module in sorted(modules & plugins_before):
			meta = plugins_meta["module"].get(module)
			prefix = f"{plugin_doc_link(meta)}: " if meta else ""
			text = normalize_subject(commit.subject, commit.files, refs)
			# Drop redundant "csv:" or "csv reader:" prefix when the plugin
			# link already identifies the format.
			if meta and re.match(
				rf"^`?{re.escape(meta.lname)}`?\b|^`?{re.escape(meta.name)}`?\b",
				text,
				re.IGNORECASE,
			):
				text = re.sub(
					rf"^`?{re.escape(meta.lname)}`?(?:\s+reader)?\s*:\s*",
					"",
					text,
					flags=re.IGNORECASE,
				)
			entries.append(
				NoteEntry(
					section=section,
					subsection=subsection,
					text=f"- {prefix}{text}",
					sort_key=module,
				),
			)
		if entries:
			return entries

	entries.append(
		NoteEntry(
			section=section,
			subsection=subsection,
			text=f"- {normalize_subject(commit.subject, commit.files, refs)}",
			sort_key=commit.subject.lower(),
		),
	)
	return entries


def find_new_contributors(
	prev_tag: str,
	end_ref: str,
	refs: dict[str, GitHubReference],
) -> list[tuple[str, str, str]]:
	authors_raw = run_git(
		"log",
		f"{prev_tag}..{end_ref}",
		"--no-merges",
		"--format=%an%x1f%ae",
	)
	seen: set[str] = set()
	contributors: list[tuple[str, str, str]] = []
	for line in authors_raw.splitlines():
		if not line.strip():
			continue
		name, email = line.split("\x1f", 1)
		key = email.lower()
		if key in seen:
			continue
		seen.add(key)
		in_cycle = run_git(
			"log",
			f"{prev_tag}..{end_ref}",
			f"--author={email}",
			"--format=%H",
			"-1",
		).strip()
		if not in_cycle:
			continue
		prior = subprocess.run(
			["git", "log", prev_tag, f"--author={email}", "--format=%H", "-1"],
			cwd=ROOT,
			capture_output=True,
			text=True,
			check=True,
		)
		if prior.stdout.strip():
			continue
		first_subject = run_git("log", "-1", "--format=%s", in_cycle).strip()
		pr_nums = ISSUE_PR_RE.findall(first_subject)
		pr_link = ""
		if pr_nums:
			pr_link = (
				f" in {github_reference_link(pr_nums[0], refs, include_author=False)}"
			)
		username = guess_github_username(name, email)
		contributors.append((username, name, pr_link))
	return sorted(contributors, key=lambda item: item[0].lower())


def guess_github_username(name: str, email: str) -> str:
	# Co-authored-by or author lines sometimes include @handle in commit body;
	# fall back to name heuristic.
	for ref in (email.split("@", maxsplit=1)[0], name.replace(" ", "")):
		if re.fullmatch(r"[A-Za-z0-9_-]+", ref):
			return ref
	return name.replace(" ", "")


def referenced_numbers(commits: list[Commit]) -> set[str]:
	return {
		number for commit in commits for number in ISSUE_PR_RE.findall(commit.subject)
	}


def uncommitted_entries() -> list[NoteEntry]:
	status = subprocess.run(
		["git", "status", "--porcelain"],
		cwd=ROOT,
		capture_output=True,
		text=True,
		check=True,
	)
	if status.returncode != 0 or not status.stdout.strip():
		return []
	entries: list[NoteEntry] = []
	for line in status.stdout.splitlines():
		if len(line) < 4:
			continue
		path = line[3:].strip()
		if path.startswith("doc/releases/"):
			continue
		entries.append(
			NoteEntry(
				section="other",
				subsection=None,
				text=f"- *(uncommitted)* `{path}`",
				sort_key=path,
			),
		)
	diff_stat = subprocess.run(
		["git", "diff", "--stat"],
		cwd=ROOT,
		capture_output=True,
		text=True,
		check=True,
	)
	if diff_stat.stdout.strip():
		entries.append(
			NoteEntry(
				section="other",
				subsection=None,
				text=(
					"- *(uncommitted)* working tree has unstaged changes"
					" — review `git diff` before tagging"
				),
				sort_key="zzz-uncommitted",
			),
		)
	return entries


def render(entries: list[NoteEntry], prev_tag: str, version: str) -> str:
	by_section: dict[str, list[NoteEntry]] = {key: [] for key, _ in SECTIONS}
	for entry in entries:
		if entry.section in by_section:
			by_section[entry.section].append(entry)

	lines = ["## What's Changed", ""]

	def append_section(section_key: str, heading: str) -> None:
		items = by_section.get(section_key, [])
		if not items:
			return
		lines.append(heading)
		lines.append("")
		for item in sorted(items, key=lambda e: e.sort_key or e.text.lower()):
			lines.append(item.text)  # noqa: PERF401
		lines.append("")

	append_section("compatibility", SECTION_HEADINGS["compatibility"])
	for bug_key in ("bug_security", "bug_core", "bug_plugins", "bug_ui"):
		append_section(bug_key, SECTION_HEADINGS[bug_key])

	feature_items = (
		by_section["feature_formats"]
		+ by_section["feature_cli"]
		+ by_section["feature_ui"]
	)
	if feature_items:
		lines += (SECTION_HEADINGS["features"], "")
		for section_key, subsection_title in (
			("feature_formats", "New read/write format functionalities"),
			("feature_cli", "New command-line features"),
			("feature_ui", "New user interface features"),
		):
			items = by_section[section_key]
			if not items:
				continue
			lines += (f"#### {subsection_title}", "")
			for item in sorted(items, key=lambda e: e.sort_key or e.text.lower()):
				lines.append(item.text)  # noqa: PERF401
			lines.append("")

	append_section("improvements", SECTION_HEADINGS["improvements"])
	append_section("other", SECTION_HEADINGS["other"])

	contributors = by_section.get("contributors", [])
	if contributors:
		lines += (SECTION_HEADINGS["contributors"], "")
		for item in contributors:
			lines.append(item.text)  # noqa: PERF401
		lines.append("")

	compare = f"{GITHUB}/compare/{prev_tag}...{version}"
	lines += (f"**Full Changelog**: [{compare}]({compare})", "")
	return "\n".join(lines)


def confirm_overwrite(path: Path) -> bool:
	if not sys.stdin.isatty():
		print(f"Error: {path} already exists", file=sys.stderr)
		return False
	while True:
		try:
			answer = input(f"Overwrite existing file {path}? [y/n]: ").strip().lower()
		except (EOFError, KeyboardInterrupt):
			print("\nAborted")
			return False
		if answer in {"y", "yes"}:
			return True
		if answer in {"n", "no", ""}:
			print("Aborted")
			return False


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Create doc/releases/VERSION.md using release-notes conventions",
	)
	parser.add_argument("version", help="Release version (tag name), e.g. 5.4.2")
	parser.add_argument(
		"--prev-tag",
		help="Previous release tag (default: tag before VERSION)",
	)
	parser.add_argument(
		"--end-ref",
		help="End git ref (default: VERSION tag if it exists, else HEAD)",
	)
	parser.add_argument(
		"--include-uncommitted",
		action="store_true",
		help="Append bullets for uncommitted changes (per release-notes rules)",
	)
	parser.add_argument(
		"--no-github-lookup",
		action="store_true",
		help="Use cached GitHub metadata only; do not make API requests",
	)
	parser.add_argument(
		"-o",
		"--output",
		type=Path,
		help="Output path (default: doc/releases/VERSION.md)",
	)
	args = parser.parse_args()

	prev_tag = resolve_prev_tag(args.version, args.prev_tag)
	end_ref = args.end_ref or resolve_end_ref(args.version)
	output_path = args.output or (RELEASES_DIR / f"{args.version}.md")

	if output_path.exists() and not confirm_overwrite(output_path):
		sys.exit(1)

	plugins_meta = load_plugins_meta()
	plugins_before = plugins_at_ref(prev_tag)
	commits = collect_commits(prev_tag, end_ref)
	github_refs = GitHubRefResolver(
		GITHUB_REFS_CACHE,
		fetch=not args.no_github_lookup,
	).resolve_all(referenced_numbers(commits))

	entries: list[NoteEntry] = []
	for commit in commits:
		if is_skip_commit(commit):
			continue
		section, subsection = categorize_commit(commit, plugins_before, plugins_meta)
		entries.extend(
			commit_to_entries(
				commit,
				section,
				subsection,
				plugins_before,
				plugins_meta,
				github_refs,
			),
		)

	if args.include_uncommitted:
		entries.extend(uncommitted_entries())

	seen_text: set[str] = set()
	deduped: list[NoteEntry] = []
	for entry in entries:
		if entry.text in seen_text:
			continue
		seen_text.add(entry.text)
		deduped.append(entry)
	entries = deduped

	for username, _name, pr_link in find_new_contributors(
		prev_tag,
		end_ref,
		github_refs,
	):
		entries.append(
			NoteEntry(
				section="contributors",
				subsection=None,
				text=(
					f"- [@{username}](https://github.com/{username})"
					f" made their first contribution{pr_link}"
				),
				sort_key=username.lower(),
			),
		)

	content = render(entries, prev_tag, args.version)

	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text(content, encoding="utf-8")
	print(f"Created {output_path}")
	print(f"  Range: {prev_tag}..{end_ref}")
	print("Review and edit bullets before publishing.")


if __name__ == "__main__":
	main()
