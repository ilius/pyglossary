# QuickDic 6 sort key

Notes on the `quickdic6` sort key, how it relates to the QuickDic index order,
and why its tests differ from the Zim sort-key tests.

## Where QuickDic sorting happens

QuickDic does not sort its stored entries. The Writer appends entries to
`QuickDic.htmls` in input order and stores that list as-is. The format-defined
order lives only in the generated index (`QuickDic.indices`).

`QuickDic.add_index` builds that index:

1. Collect tokens from `pairs` and `htmls`, strip them, and normalize them with
   the ICU `Transliterator` built from `normalizer_rules`.
2. Insert synonym tokens for any token present in the synonyms map.
3. Sort tokens with `Comparator.compare`.
4. Merge adjacent tokens with the same original string.

The Writer is `sortOnWrite = INTERNAL`: it ignores `--sort` / `--sort-key` and
always builds the index itself.

## Sort key implementation

`pyglossary/sort_modules/quickdic6.py` provides `normal` and `sqlite` factories
registered as `quickdic6` in `sort_keys.py`. It reuses
`pyglossary/plugins/quickdic6/comparator.py` so the key stays in sync with the
format.

The key is the ICU collation key of the normalized headword, produced by
`Comparator.sort_key_parts`. ICU sort keys can be compared bytewise and give
the same order as `Collator.compare`.

Options:

- `language` (or `iso`): locale code, default `en`.
- `normalizer_rules`: ICU transliteration rules, defaulting to the same rules
  the Writer uses. `en` gets the custom `&z<ȝ` collator in `Comparator`.
- `version`: QuickDic format version, default `6`.

`language` and `version` are not exposed as CLI options. The sort key is
currently only reachable through `sortKeyName="quickdic6"`, which uses the
defaults.

## Why the round-trip test differs from Zim

For Zim, the Writer stores entries in libzim path order, and the Reader walks
entries by ID, so `txt -> zim -> txt` returns the sorted order. The Zim test
can therefore compare that round trip directly with `sortKeyName="zim"`.

For QuickDic 6, the Reader yields `pairs`, `texts`, and `htmls` in stored order.
The Writer does not reorder them, so `txt -> quickdic6 -> txt` keeps the source
order, not the index order.

Tests therefore use two checks:

- `test_sort_key_quickdic6_matches_index_order` compares the sorted txt
  headwords with the token order in the generated index
  (`QuickDic.indices[0][6]`).
- `test_convert_txt_quickdic6_txt_preserves_order` asserts that the round trip
  keeps the stored order.

Comparing the round trip to the sort key would require either changing the
Reader to iterate in index order or changing the Writer to store entries in
index order. Both would change existing behavior and fixture outputs.

## Duplicates, alternates, and synonyms

The tests use `100-en-de-v4.txt`, which has no duplicate primary headwords and
no `|` alternates. This avoids several mismatches:

- Duplicate headwords are merged in the index, and a primary-headword sort key
  cannot reproduce that merge.
- Alternate headwords become synonyms in the index. They are inserted among the
  tokens, so a key that only uses `words[0]` cannot place them.
- The Reader reconstructs synonyms from the index, including derived
  normalized forms (for example spaces removed by `' ' > ;`). A QuickDic round
  trip can therefore add alternate terms that were not in the source. The
  round-trip test compares only the primary term (`entry.l_term[0]`).

## QuickDic 7

`Comparator` already supports version 7. The difference is in `compare`:

- Version 6: compare the normalized strings and return the result.
- Version 7 and later:
  1. Compare normalized strings with `-` removed and `þ`/`Þ` folded to
     `th`/`Th`.
  2. If equal, compare the normalized strings.
  3. If still equal, compare the original strings as a case-sensitive
     tie-break.

`sort_key_parts` returns one collation key for versions below 7, and three keys
(dash-folded normalized, normalized, original) for version 7 and later. Tuple
ordering of those parts matches `Comparator.compare`, and the SQLite variant
maps them to three `BLOB` columns.

This v7 path is currently library-only:

- The Writer always writes version 6.
- The Reader uses the index stored in the file, so it never recomputes the
  sort order.
- There is no CLI way to pass `version=7` to the sort key.
- No v7 sort test exists yet.

## Verifying the key

The sort key was checked against `Comparator.compare` directly for versions 6
and 7 using terms that exercise dashes, `þ`/`Þ`, accents, case, and spaces. For
both versions, sorting with `sort_key_parts` produced the same order as sorting
with `compare`.
