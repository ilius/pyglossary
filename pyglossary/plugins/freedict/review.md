# FreeDict plugin review

Scope: `parser.py`, `reader.py`, `utils.py`, `options.py`, `__init__.py` in this directory, the FreeDictMarkdown plugin (`pyglossary/plugins/freedict_md/`), `doc/p/freedict.md`, `doc/p/freedict_md.md`, `tests/g_freedict_test.py`, and `tests/g_freedict_md_test.py`.

Status: `tests/g_freedict_test.py` (14/14) and `tests/g_freedict_md_test.py` (11/11) pass; `ruff check` and `mypy` are clean for these modules; `freedict_md` plugin coverage is 86%.

## Tests and docs

2. **`auto_comma` is not tested**: `test_convert_tei_txt_1` runs with `auto_comma` False and True against the same expected output. The two runs produce identical output for `100-en-de`, so the option is not exercised. No fixture covers non-Latin separators.
3. **Uncovered options and paths**: comments and include cycles are covered for both readers. Still without tests: `word_title`, the colour options, `example_padding`, and explicit `auto_rtl` behavior.

## Suggested order

1. Add a non-Latin `auto_comma` fixture and tests for the uncovered options; rename fixtures per CLAUDE.md and regenerate outputs (items 2, 3, 4, 5).
2. Keep the duplicated Markdown renderer/file-I/O in sync with `freedict/reader.py` when HTML behavior changes (item 1; duplication is intentional).
