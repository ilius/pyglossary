#!/usr/bin/env bash
# Fail if any *new or changed* blob (vs base) exceeds MAX_BYTES.
# Compares file contents at BASE and HEAD SHAs; unchanged blobs are ignored.

set -euo pipefail

MAX_BYTES="${MAX_BLOB_BYTES:-102400}"

if [[ "${GITHUB_EVENT_NAME:-}" == "pull_request" ]]; then
	BASE_SHA="${GITHUB_PR_BASE_SHA:?}"
	HEAD_SHA="${GITHUB_PR_HEAD_SHA:?}"
elif [[ "${GITHUB_EVENT_NAME:-}" == "push" ]]; then
	HEAD_SHA="${GITHUB_SHA:?}"
	BEFORE_SHA="${GITHUB_PUSH_BEFORE_SHA:?}"
	if [[ "${BEFORE_SHA}" == "0000000000000000000000000000000000000000" ]]; then
		DEFAULT_BRANCH="${GITHUB_DEFAULT_BRANCH:?}"
		git fetch origin "${DEFAULT_BRANCH}"
		BASE_SHA="$(git merge-base "origin/${DEFAULT_BRANCH}" "${HEAD_SHA}")"
	else
		BASE_SHA="${BEFORE_SHA}"
	fi
else
	echo "Unsupported event: ${GITHUB_EVENT_NAME:-}" >&2
	exit 2
fi

fail=0
while IFS= read -r path || [[ -n "${path}" ]]; do
	[[ -n "${path}" ]] || continue
	if ! git cat-file -e "${HEAD_SHA}:${path}" 2>/dev/null; then
		continue
	fi
	otype="$(git cat-file -t "${HEAD_SHA}:${path}" 2>/dev/null || true)"
	[[ "${otype}" == "blob" ]] || continue
	head_blob="$(git rev-parse "${HEAD_SHA}:${path}")"
	base_blob=""
	if git cat-file -e "${BASE_SHA}:${path}" 2>/dev/null; then
		btype="$(git cat-file -t "${BASE_SHA}:${path}" 2>/dev/null || true)"
		if [[ "${btype}" == "blob" ]]; then
			base_blob="$(git rev-parse "${BASE_SHA}:${path}")"
		fi
	fi
	if [[ "${head_blob}" == "${base_blob}" ]]; then
		continue
	fi
	size="$(git cat-file -s "${head_blob}")"
	if ((size > MAX_BYTES)); then
		printf 'Blob too large (%d bytes > %d): %s at %s\n' "${size}" "${MAX_BYTES}" "${path}" "${HEAD_SHA}" >&2
		fail=1
	fi
done < <(git diff --name-only "${BASE_SHA}" "${HEAD_SHA}" 2>/dev/null || true)

exit "${fail}"
