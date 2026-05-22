#!/usr/bin/env python3
r"""
Run GitHub Actions workflows that use Ubuntu runners locally via Docker (nektos/act).

Requires:
  - Docker running
  - act: https://github.com/nektos/act
  - PyYAML (see requirements.txt)

By default this skips publishing (PyPI), CodeQL (slow / special GitHub integration), and
any Ubuntu job that depends on a non-Ubuntu job (e.g. release jobs after macOS/Windows
builds).

Errors:
test*
	Unable to locate package dictzip
max-blob-size.yml:
	[command]/usr/bin/git rev-parse --verify --quiet \
		167d4a4ac82674fe61b742491cca0449fc2a3dff^{object}
	[command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune \
		--no-recurse-submodules origin 167d4a4ac82674fe61b742491cca0449fc2a3dff
	fatal: remote error: upload-pack: not our ref 167d4a4ac82674fe61b742491cca0449fc2a3dff
	The process '/usr/bin/git' failed with exit code 128
	Waiting 18 seconds before trying again

"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from datetime import timedelta

try:
	import yaml
except ImportError:
	print("PyYAML is required: pip install pyyaml", file=sys.stderr)
	sys.exit(1)


UBUNTU_PATTERN = re.compile(r"ubuntu-[\w.]+|^ubuntu$", re.IGNORECASE)

skip_workflows: set[str] = {
	"codeql.yml",
	"pypi-release.yml",
	"mdformat.yml",
	"max-blob-size.yml",  # FIXME
}


def _workflow_files(root: Path) -> list[Path]:
	wf_dir = root / ".github" / "workflows"
	if not wf_dir.is_dir():
		return []
	files: list[Path] = []
	for pat in ("*.yml", "*.yaml"):
		files.extend(sorted(wf_dir.glob(pat)))
	return sorted(set(files))


def _normalize_needs(raw: Any) -> list[str]:
	if raw is None:
		return []
	if isinstance(raw, str):
		return [raw]
	if isinstance(raw, list):
		return [str(x) for x in raw]
	return []


def _ubuntu_from_matrix_os(job: dict[str, Any]) -> bool | None:
	"""Classify matrix.os as all Ubuntu, all non-Ubuntu, or mixed/unknown."""
	strat = job.get("strategy") or {}
	matrix = strat.get("matrix") or {}
	if not isinstance(matrix, dict) or "os" not in matrix:
		return None
	oses = matrix["os"]
	if not isinstance(oses, list):
		oses = [oses]
	lowered = [str(o).lower() for o in oses]
	ubuntu = [o for o in lowered if "ubuntu" in o or o.startswith("ubuntu-")]
	if len(ubuntu) == len(lowered):
		return True
	if len(ubuntu) == 0:
		return False
	return None


def _job_is_ubuntu(job_id: str, job: dict[str, Any]) -> bool:
	ro = job.get("runs-on")
	if ro is None:
		return False
	if isinstance(ro, str):
		s = ro.strip()
		if "${{" in s and "matrix.os" in s:
			u = _ubuntu_from_matrix_os(job)
			if u is True:
				return True
			if u is False:
				return False
			print(
				f"  warning: job {job_id!r} uses matrix.os; "
				f"could not classify — skipping",
				file=sys.stderr,
			)
			return False
		sl = s.lower()
		return sl == "ubuntu-latest" or bool(UBUNTU_PATTERN.match(s))
	return False


def _ubuntu_runnable_jobs(jobs: dict[str, Any]) -> list[str]:
	"""Jobs on Ubuntu that do not (transitively) depend on a non-Ubuntu job."""

	def is_ubuntu(jid: str) -> bool:
		return _job_is_ubuntu(jid, jobs[jid])

	def runnable(jid: str, seen: set[str]) -> bool:
		if jid in seen:
			return False
		seen.add(jid)
		if jid not in jobs or not is_ubuntu(jid):
			return False
		for n in _normalize_needs(jobs[jid].get("needs")):
			if not is_ubuntu(n):
				return False
			if not runnable(n, seen):
				return False
		return True

	return sorted(jid for jid in jobs if runnable(jid, set()))


def _workflow_triggers(raw: dict[str, Any]) -> Any:
	"""Return the workflow `on:` mapping (PyYAML parses bare `on` as bool True)."""
	return raw.get("on", raw.get(True))


def _pick_act_event(events: Any) -> str:
	if not events or not isinstance(events, dict):
		return "push"
	if "workflow_dispatch" in events:
		return "workflow_dispatch"
	if "pull_request" in events:
		return "pull_request"
	if "push" in events:
		return "push"
	for key in ("schedule", "release", "repository_dispatch"):
		if key in events:
			return "workflow_dispatch"
	return "workflow_dispatch"


def _default_platform_args() -> list[str]:
	env = os.environ.get("ACT_PLATFORM")
	if env:
		arg = env.strip()
		if arg.startswith("ubuntu-latest="):
			return ["-P", arg]
		return ["-P", f"ubuntu-latest={arg}"]
	return [
		"-P",
		"ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-22.04",
	]


@dataclass(frozen=True)
class _ActConfig:
	root: Path
	act_invocation: str
	platform_args: list[str]
	act_extra: list[str]
	dry_run: bool


@dataclass
class JobResult:
	succeed: bool
	duration: timedelta
	path: Path


def _resolve_act_path(act_bin: str) -> str | None:
	if shutil.which(act_bin):
		return act_bin
	if os.path.isfile(act_bin) and os.access(act_bin, os.X_OK):
		return act_bin
	return None


def _run_workflow_jobs(
	wf: Path,
	rel: Path,
	event: str,
	ubuntu_jobs: list[str],
	cfg: _ActConfig,
) -> int:
	"""Run or list act commands per job. Returns exit_code."""
	base_cmd: list[str] = [
		cfg.act_invocation,
		event,
		"-W",
		str(wf),
	]
	base_cmd.extend(cfg.platform_args)
	base_cmd.extend(cfg.act_extra)

	print(f"\n== {rel} ==")
	print(f"    event={event} jobs={','.join(ubuntu_jobs)}")
	for jid in ubuntu_jobs:
		cmd = [*base_cmd, "-j", jid]
		print("    ", " ".join(cmd))
		if cfg.dry_run:
			continue
		r = subprocess.run(cmd, cwd=cfg.root, env=os.environ.copy(), check=False)
		if r.returncode != 0:
			msg = f"act failed for {rel} job {jid!r} (exit {r.returncode})"
			print(msg, file=sys.stderr)
			return r.returncode
	return 0


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"--repo-root",
		type=Path,
		default=Path.cwd(),
		help="Repository root (default: current directory)",
	)
	parser.add_argument(
		"--act-bin",
		default=os.environ.get("ACT_BIN", "act"),
		help="act executable (default: act or $ACT_BIN)",
	)
	parser.add_argument(
		"--event",
		choices=("workflow_dispatch", "pull_request", "push"),
		help="Force act event type (default: inferred per workflow)",
	)
	parser.add_argument(
		"--dry-run",
		action="store_true",
		help="Print act commands without running",
	)
	parser.add_argument(
		"--no-default-platform",
		action="store_true",
		help="Do not pass -P ubuntu-latest=catthehacker image",
	)
	args, act_extra = parser.parse_known_args()

	root = args.repo_root.resolve()
	if not (root / ".git").exists() and not (root / ".github").exists():
		print(f"Not a repository root (missing .git/.github): {root}", file=sys.stderr)
		return 1

	act_path = _resolve_act_path(args.act_bin)
	need_act = not args.dry_run
	if need_act and not act_path:
		print(
			"act is not installed or not on PATH. Install: "
			"https://github.com/nektos/act#installation",
			file=sys.stderr,
		)
		return 1

	platform_args: list[str] = (
		[] if args.no_default_platform else _default_platform_args()
	)

	act_invocation = act_path or args.act_bin
	cfg = _ActConfig(
		root=root,
		act_invocation=act_invocation,
		platform_args=platform_args,
		act_extra=act_extra,
		dry_run=args.dry_run,
	)
	result: list[JobResult] = []
	for wf in _workflow_files(root):
		if wf.name in skip_workflows:
			continue

		try:
			raw = yaml.safe_load(wf.read_text(encoding="utf-8")) or {}
		except yaml.YAMLError as e:
			print(f"{wf}: YAML error: {e}", file=sys.stderr)
			return 1

		if not isinstance(raw, dict):
			continue
		jobs = raw.get("jobs") or {}
		if not isinstance(jobs, dict):
			continue
		ubuntu_jobs = _ubuntu_runnable_jobs(jobs)
		if not ubuntu_jobs:
			continue

		event = args.event or _pick_act_event(_workflow_triggers(raw))
		rel = wf.relative_to(root) if wf.is_relative_to(root) else wf
		t0 = datetime.now()
		try:
			code = _run_workflow_jobs(wf, rel, event, ubuntu_jobs, cfg)
		except KeyboardInterrupt:
			code = 1
		result.append(
			JobResult(
				succeed=code == 0,
				duration=datetime.now() - t0,
				path=wf,
			)
		)

	print()
	print("-----------------------------------------------------------")
	print()
	for res in result:
		print(
			f"{'✅' if res.succeed else '❌'} "
			f"{res.duration.total_seconds(): 5.1f} sec  {res.path}",
		)

	return 0


if __name__ == "__main__":
	sys.exit(main())
