# FreeDict plugin review

Scope: `parser.py`, `reader.py`, `formatter.py`, `html_formatter.py`, `md_formatter.py`, `utils.py`, `options.py`, `__init__.py` in this directory, `doc/p/freedict.md`, and `tests/g_freedict_test.py`.

Status: `tests/g_freedict_test.py` passes for both HTML and Markdown definitions; `ruff check` and `mypy` are clean for these modules.

## Tests and docs

2. **`auto_comma` is not tested**: `test_convert_tei_txt_1` runs with `auto_comma` False and True against the same expected output. The two runs produce identical output for `100-en-de`, so the option is not exercised. No fixture covers non-Latin separators.
3. **Uncovered options and paths**: comments and include cycles are covered for both output formats. Still without tests: `word_title`, the colour options, `example_padding`, and explicit `auto_rtl` behavior.

## Suggested order

1. Add a non-Latin `auto_comma` fixture and tests for the uncovered options; rename fixtures per CLAUDE.md and regenerate outputs (items 2, 3, 4, 5).
2. TEI entries are laid out into the neutral tree in `freedict/document.py` by `freedict/layout.py`; formatting is a generic dispatch in `freedict/formatter.py` with HTML and Markdown implementations in `freedict/html_formatter.py` and `freedict/md_formatter.py`, and file I/O lives in `freedict/reader.py`. The single reader chooses the formatter from the `defiFormat` option.
