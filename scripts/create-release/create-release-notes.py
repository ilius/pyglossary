#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate doc/releases/VERSION.md from git history."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = "ilius/pyglossary"
GITHUB = f"https://github.com/{REPO}"
ROOT = Path(__file__).resolve().parent.parent.parent
PLUGINS_META = ROOT / "plugins-meta" / "index.json"
RELEASES_DIR = ROOT / "doc" / "releases"

SKIP_SUBJECT_RE = re.compile(
	r"^(version \d|add doc/releases/|update doc/releases/|ignore ruff|"
	r"fix ruff|fix mypy|remove unused type ignore)",
	re.IGNORECASE,
)
ISSUE_PR_RE = re.compile(r"(?<![`\w])#(\d+)(?![`\w])")
VERSION_COMMIT_RE = re.compile(r"^version \d", re.IGNORECASE)
SECURITY_RE = re.compile(
	r"security|malicious|path traversal|absolute path|\.\./|refuse absolute",
	re.IGNORECASE,
)
COMPAT_RE = re.compile(
	r"python_requires|require python|breaking|compat|default (?:gui|is now)|"
	r"no longer|deprecated",
	re.IGNORECASE,
)
FIX_RE = re.compile(r"\bfix\b|bug fix|regression", re.IGNORECASE)
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
	r"^ui[_:]|^ui_gtk|^ui_tk|^ui_qt|gtk|tkinter|tk wizard|qt6|about dialog|"
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
		if match:
			modules.add(match.group(1))
	return modules


def link_issues_and_prs(text: str) -> str:
	def repl(match: re.Match[str]) -> str:
		num = match.group(1)
		kind: str
		if "pull" in text.lower() or "pr" in text.lower():  # noqa: SIM108
			kind = "pull"
		else:
			kind = "issues"
		# Prefer pull when commit mentions PR explicitly;
		# otherwise issues (GitHub redirects).
		if re.search(rf"\bPR\s*{num}\b", text, re.IGNORECASE) or re.search(
			rf"pull\s*{num}\b", text, re.IGNORECASE
		):
			kind = "pull"
		return f"[#{num}]({GITHUB}/{kind}/{num})"

	return ISSUE_PR_RE.sub(repl, text)


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
	suffix = f" ({issue_links})" if issue_links else ""
	return (
		f"- {link} {role}{suffix} — {desc.rstrip('.')}. "
		f"*Use case:* (describe why someone would convert this format with PyGlossary)"
	)


def normalize_subject(subject: str) -> str:
	text = subject.strip()
	text = re.sub(r"^[a-f0-9]{8}\s+", "", text)
	if text and text[0].islower():
		text = text[0].upper() + text[1:]
	return link_issues_and_prs(text)


def is_skip_commit(commit: Commit) -> bool:
	if SKIP_SUBJECT_RE.match(commit.subject):
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


def categorize_commit(  # noqa: C901, PLR0912
	commit: Commit,
	plugins_before: set[str],
	_plugins_meta: dict[str, dict[str, PluginMeta]],
) -> tuple[str, str | None]:
	subject = commit.subject
	files = commit.files
	modules = plugin_modules_in_files(files)
	new_modules = modules - plugins_before
	existing_modules = modules & plugins_before

	ui_files = any("/ui/" in f.replace("\\", "/") for f in files)
	plugin_files = bool(modules)
	core_files = any(
		p in f.replace("\\", "/")
		for f in files
		for p in (
			"pyglossary/glossary.py",
			"pyglossary/plugin_handler.py",
			"pyglossary/entry",
			"pyglossary/core.py",
			"pyglossary/argparse",
			"pyglossary/ui/argparse",
			"pyglossary/ui/main.py",
		)
	)

	if is_doc_or_meta_commit(files, subject):
		return "other", None

	if COMPAT_RE.search(subject) or (
		any(f.endswith(("setup.py", "pyproject.toml")) for f in files)
		and COMPAT_RE.search(subject)
	):
		return "compatibility", None

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
		if ui_files or (UI_RE.search(subject) and "ui_cmd" in subject.lower()):
			return "bug_ui", None
		if core_files:
			return "bug_core", None
		if plugin_files and new_modules:
			return "feature_formats", "New read/write format functionalities"
		if plugin_files:
			return "bug_plugins", None
		return "bug_core", None

	if new_modules and (
		NEW_FORMAT_RE.search(subject) or re.search(r"\badd\b", subject, re.IGNORECASE)
	):
		return "feature_formats", "New read/write format functionalities"

	if UI_LAUNCHER_FLAG_RE.search(subject):
		return "feature_ui", "New user interface features"

	if (
		CLI_RE.search(subject)
		and not UI_RE.search(subject)
		and (
			"view-glossary" in subject
			or "diff-glossary" in subject
			or subject.lower().startswith("add --")
		)
	):
		return "feature_cli", "New command-line features"

	if (UI_RE.search(subject) or (ui_files and "fix" not in subject.lower())) and (
		"add" in subject.lower()
		or "support" in subject.lower()
		or "drag-and-drop" in subject.lower()
	):
		return "feature_ui", "New user interface features"

	if IMPROVE_RE.search(subject) and (existing_modules or plugin_files):
		return "improvements", None

	if re.search(r"\bsupport\b", subject, re.IGNORECASE) and existing_modules:
		return "improvements", None

	if OTHER_RE.search(subject) or not (plugin_files or ui_files or core_files):
		return "other", None

	if "add" in subject.lower():
		if ui_files or UI_RE.search(subject):
			return "feature_ui", "New user interface features"
		if CLI_RE.search(subject):
			return "feature_cli", "New command-line features"
		if new_modules:
			return "feature_formats", "New read/write format functionalities"

	return "other", None


def commit_to_entries(
	commit: Commit,
	section: str,
	subsection: str | None,
	plugins_before: set[str],
	plugins_meta: dict[str, dict[str, PluginMeta]],
) -> list[NoteEntry]:
	modules = plugin_modules_in_files(commit.files)
	new_modules = sorted(modules - plugins_before)
	entries: list[NoteEntry] = []

	if section == "feature_formats" and new_modules:
		for module in new_modules:
			meta = plugins_meta["module"].get(module)
			if meta is None:
				continue
			issue_links = " ".join(
				f"[#{n}]({GITHUB}/pull/{n})"
				if "pull" in commit.subject.lower()
				else f"[#{n}]({GITHUB}/issues/{n})"
				for n in ISSUE_PR_RE.findall(commit.subject)
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
			text = normalize_subject(commit.subject)
			# Drop redundant "csv reader:" prefix when plugin link is present.
			if meta and re.match(
				rf"^{re.escape(meta.lname)}\b|^{re.escape(meta.name)}\b",
				text,
				re.IGNORECASE,
			):
				text = re.sub(
					rf"^{re.escape(meta.lname)}\s*reader:\s*",
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
			text=f"- {normalize_subject(commit.subject)}",
			sort_key=commit.subject.lower(),
		),
	)
	return entries


def find_new_contributors(prev_tag: str, end_ref: str) -> list[tuple[str, str, str]]:
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
			pr_link = f" in [#{pr_nums[0]}]({GITHUB}/pull/{pr_nums[0]})"
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
					" — review `git diff` before tagging",
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
		lines.append(SECTION_HEADINGS["features"])
		lines.append("")
		for section_key, subsection_title in (
			("feature_formats", "New read/write format functionalities"),
			("feature_cli", "New command-line features"),
			("feature_ui", "New user interface features"),
		):
			items = by_section[section_key]
			if not items:
				continue
			lines.append(f"#### {subsection_title}")
			lines.append("")
			for item in sorted(items, key=lambda e: e.sort_key or e.text.lower()):
				lines.append(item.text)  # noqa: PERF401
			lines.append("")

	append_section("improvements", SECTION_HEADINGS["improvements"])
	append_section("other", SECTION_HEADINGS["other"])

	contributors = by_section.get("contributors", [])
	if contributors:
		lines.append(SECTION_HEADINGS["contributors"])
		lines.append("")
		for item in contributors:
			lines.append(item.text)  # noqa: PERF401
		lines.append("")

	compare = f"{GITHUB}/compare/{prev_tag}...{version}"
	lines.append(f"**Full Changelog**: [{compare}]({compare})")
	lines.append("")
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
		if answer in ("y", "yes"):
			return True
		if answer in ("n", "no", ""):
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

	entries: list[NoteEntry] = []
	for commit in commits:
		if is_skip_commit(commit):
			continue
		section, subsection = categorize_commit(commit, plugins_before, plugins_meta)
		entries.extend(
			commit_to_entries(commit, section, subsection, plugins_before, plugins_meta),
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

	for username, _name, pr_link in find_new_contributors(prev_tag, end_ref):
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
	print(
		"Review and edit bullets "
		"(especially *Use case:* for new formats) before publishing."
	)


if __name__ == "__main__":
	main()
