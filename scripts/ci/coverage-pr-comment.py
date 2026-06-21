#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def repo_root() -> Path:
	myDir = Path(__file__).resolve()
	assert len(myDir.parents) > 3, f"{myDir=}"
	return myDir.parents[2]


def run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
	subprocess.run(cmd, check=True, cwd=cwd, env=env)


def load_summary(path: Path) -> dict[str, float]:
	with path.open(encoding="utf-8") as file:
		data = json.load(file)
	return {key: float(data[key]) for key in ("main", "ui", "combined")}


def fmt_pct(value: float) -> str:
	return f"{value:.1f}%"


def fmt_delta(base: float, head: float) -> str:
	delta = head - base
	sign = "+" if delta >= 0 else ""
	return f"{sign}{delta:.1f}%"


def render_comment(
	base: dict[str, float],
	head: dict[str, float],
	base_branch: str,
) -> str:
	rows = (
		("Main tests", "main"),
		("UI tests", "ui"),
		("Combined", "combined"),
	)
	lines = [
		"## Coverage overview",
		"",
		f"| Suite | branch {base_branch} | This PR | Δ |",
		"| --- | ---: | ---: | ---: |",
	]
	for label, key in rows:
		base_value = base[key]
		head_value = head[key]
		lines.append(
			f"| {label} | {fmt_pct(base_value)} | {fmt_pct(head_value)} "
			f"| {fmt_delta(base_value, head_value)} |",
		)
	lines.extend(
		[
			"",
			(
				"_Overall line coverage on Python 3.12. "
				"Download workflow artifacts for the HTML report._"
			),
		],
	)
	return "\n".join(lines) + "\n"


def set_github_output(name: str, value: str) -> None:
	output_file = os.environ.get("GITHUB_OUTPUT")
	if not output_file:
		return
	with open(output_file, "a", encoding="utf-8") as file:
		file.write(f"{name}={value}\n")


def main() -> None:
	root = repo_root()
	coverage_dir = root / "artifacts" / "coverage"
	head_summary_path = coverage_dir / "summary.json"
	if not head_summary_path.is_file():
		print("Head coverage summary not found, skipping PR comment")
		return

	base_ref = os.environ["BASE_REF"]
	github_sha = os.environ["GITHUB_SHA"]
	head_summary_tmp = Path("/tmp/coverage-head-summary.json")
	base_summary_tmp = Path("/tmp/coverage-base-summary.json")
	head_artifacts_tmp = Path("/tmp/coverage-head-artifacts")
	collect_script_tmp = Path("/tmp/collect-coverage-head.sh")
	collect_script = root / "scripts" / "ci" / "collect-coverage.sh"

	shutil.copy2(collect_script, collect_script_tmp)
	shutil.copy2(head_summary_path, head_summary_tmp)
	if head_artifacts_tmp.exists():
		shutil.rmtree(head_artifacts_tmp)
	shutil.copytree(coverage_dir, head_artifacts_tmp)

	run(["git", "fetch", "origin", base_ref], cwd=root)
	run(["git", "checkout", f"origin/{base_ref}"], cwd=root)

	collect_env = {**os.environ, "COVERAGE_SKIP_HTML": "1"}
	run(["bash", str(collect_script_tmp)], cwd=root, env=collect_env)
	shutil.copy2(coverage_dir / "summary.json", base_summary_tmp)

	run(["git", "checkout", github_sha], cwd=root)
	shutil.rmtree(coverage_dir)
	shutil.copytree(head_artifacts_tmp, coverage_dir)

	comment = render_comment(
		load_summary(base_summary_tmp),
		load_summary(head_summary_tmp),
		base_ref,
	)
	(coverage_dir / "pr-comment.md").write_text(comment, encoding="utf-8")
	set_github_output("coverage_comment_ready", "true")


if __name__ == "__main__":
	main()
