# EPWING review (PR [744](https://github.com/ilius/pyglossary/pull/744))

Items from the code review that are still open.

## 1. Exact-title extractor matching is fragile

`pyglossary/plugins/epwing/converter.py:1167`

`convert_epwing_to_yomichan` now resolves the extractor with an exact lookup:

```python
extractor = extractors_map.get(subbook.title)
```

The map keys use U+3000 ideographic spaces (e.g. `"三省堂　スーパー大辞林"`),
so the decoded catalog title must match byte-for-byte. Any whitespace or
spelling variant in a real catalog (for example `"広辞苑　第六版"` with a space
vs. the listed `"広辞苑第六版"`) silently skips the whole subbook, leaving only
a log warning. This is a regression risk compared to the previous substring
match (`key in subbook.title`).

Suggested fix: normalize whitespace (e.g. `unicodedata.normalize` or strip /
collapse) on both the catalog title and the map keys before matching, and/or
keep a substring fallback for unmatched titles.

## 2. Unknown gaiji now emits U+FFFD

`pyglossary/plugins/epwing/converter.py:161`

`EpwingExtractor.translate` changed the fallback for unknown gaiji codes from
`""` to `"�"` (U+FFFD):

```python
return font.get(code, "�")
```

If an unknown gaiji code appears in a *heading*, the produced headword will
contain U+FFFD, polluting Yomichan search keys. Confirm this behavior change is
intended; otherwise restore `""` for headings (or only emit the replacement
character in definitions, not headwords).

## 3. Nested skip-code tracking in `_read_content`

`pyglossary/plugins/epwing/converter.py:688` (and surrounding logic in
`_read_content` / `_control_step`)

`skip_code` is overwritten unconditionally when any control code returns a new
skip code, and cleared only when the current code equals `skip_code`:

```python
step, new_skip = self._control_step(data, offset, code)
if new_skip is not None:
    skip_code = new_skip
elif skip_code == code:
    skip_code = None
```

Overlapping or nested ruby-style marker pairs (e.g. `0x35`/`0x55` while another
skip region is already active) would corrupt the state instead of nesting. The
simple pairs currently covered are unlikely to nest, but this should be
documented or handled explicitly.

## 4. Missing test coverage

`tests/epwing_test.py`

- No integration/smoke test against a real EPWING dictionary tree.
- The `errors="replace"` decode paths are not exercised (no malformed byte
  sequences in fixtures).
- The exact-title lookup has no fallback test, and the heading-vs-text gaiji
  behavior is untested.
