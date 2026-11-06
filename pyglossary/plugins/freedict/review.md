# FreeDict plugin review

Scope: `reader.py`, `utils.py`, `options.py`, `__init__.py` in this directory, the FreeDictMarkdown subclass (`pyglossary/plugins/freedict_md/reader.py`), `doc/p/freedict.md`, and `tests/g_freedict_test.py`.

Status at review time: `tests/g_freedict_test.py` passes (4/4), `ruff check` is clean. Each bug below was reproduced with a small TEI file.

## Confirmed bugs

9. **Empty `<ref/>` produces `bword://None`** (low)
   - `writeRef` (lines 176-182) does not handle a missing `ref.text`. The `writeRichText` path (line 455) reaches it.

10. **Entries without `<orth>` yielded with no headword** (low)
    - `getEntryByElem` yields `Entry([], ...)`. The CSV output silently omitted it. It should warn and skip.

## Design and code-quality notes

- **RTL list style differs from LTR**: the RTL branch uses `ordered=(len(senseList) > 3)` (line 864). The LTR branch always uses `ol`. Confirm whether this is intentional.
- **Suspicious mapping**: `genderMapping` contains `"adj": "adjective"` (line 144). That is a part of speech, not a gender.
- **`writeTransCit` mutates the source tree**: it moves `gramGrp` and `note` children and clears `tail` (lines 217-222). `writeExampleCit` also mutates `quote.attrib` (line 754). The comment "safe to repeat" is misleading. The code works today but is fragile.
- **Blanket type suppression**: `reader.py:12` has `# mypy: ignore-errors` for a 1,238-line file, so the type checker is effectively off here.
- **Unused or no-op pieces**:
  - `resources` option (`options.py:25`). `countResourceFiles()` returns 0 and nothing reads the option.
  - `writeSenseSense` return value (line 767) is unused.
  - `_progress` is typed `bool` but holds an int (line 1175).
  - `open()` and `loadInclude` do not close files on exceptions.
- **Discovery**: `_discoveredTags` is keyed by tag, so only the last instance is kept. Comment nodes (whose tag is a function) get stored too.
- **Typos in log messages**: "metedata" and "progress bar will not word" (around line 1018), "unrecognize" (lines 900, 913).
- **Stale docstring**: `reader.py:6-7` and `__init__.py:5` claim `.dct` support. `extensions = (".tei",)`, and nothing handles `.dct`.
- **FreeDictMarkdown coupling**: `freedict_md/reader.py` subclasses this reader and overrides `getEntryByElem`. Fixes to the shared `writeDef`, `writeRichText`, and `writeGramGroups` affect both plugins, and the TEI traversal is duplicated.

## Tests and docs

- **`auto_comma` is not tested**: `test_convert_tei_txt_1` runs with `auto_comma` False and True against the same expected output. The two runs produce identical output for `100-en-de`, so the option is not exercised. No fixture covers non-Latin separators.
- **Uncovered options and paths**: `discover`, `word_title`, colour options, `example_padding`, `auto_rtl`, comments, and include cycles have no tests.
- **Naming rules in CLAUDE.md**:
  - `100-en-de-v6.txt` and `freedict-sample-2024-12-19-v4.txt` carry version suffixes for regenerated outputs.
  - `freedict-sample-2024-12-19.tei` does not follow `<count>-<src>-<tgt>`.
- **Remote inputs**: `100-en-de.tei` and `freedict-sample-2024-12-19.tei` are not in `tests/data`. They are fetched from GitHub by CRC32 and cached in `~/.cache/pyglossary/test`, so a first run needs network access. The `100-en-de.tei` sample is a third-party file ("Sample: English-Deutsch FreeDict+WikDict dictionary"), so the provenance rule applies.
- **Stale generated doc**: `doc/p/freedict.md` has no `resources` row, while csv and tabfile docs do. Regenerate it with `./scripts/gen` after the options are settled.

## Suggested order

1. Fix the comment crash (1) and the `<def>` whitespace and separator logic (2).
2. Guard include cycles (3) and set `input_file_size` only for the top-level file (4).
3. Keep notes in example citations (5), fix the `xml:lang` mapping (7), and make `usg` handling match labels (8).
4. Add tests for comments, inline markup in `<def>`, `auto_comma` with a non-Latin fixture, and include cycles. Rename fixtures per CLAUDE.md and regenerate outputs.
5. Remove the blanket mypy suppression and the no-op `resources` option, then regenerate `doc/p/freedict.md`.
