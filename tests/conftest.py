# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import re

import pytest

collect_ignore: list[str] = []

if importlib.util.find_spec("icu") is None:
	collect_ignore.append("slob_test.py")


def pytest_collection_modifyitems(
	config: pytest.Config,
	items: list[pytest.Item],
) -> None:
	_ = config
	if importlib.util.find_spec("icu") is not None:
		return

	skip_icu = pytest.mark.skip(reason="PyICU (import icu) is not installed")

	for item in items:
		nid = item.nodeid
		if "sortLocale" in nid:
			item.add_marker(skip_icu)
		if "g_aard2_slob" in nid:
			item.add_marker(skip_icu)
		if "g_quickdic6_test" in nid:
			item.add_marker(skip_icu)
		if "g_ebook_epub2_test.py::" in nid and re.search(
			r"::TestGlossaryEPUB2::test_convert_to_epub_[1-4]\b",
			nid,
		):
			item.add_marker(skip_icu)
