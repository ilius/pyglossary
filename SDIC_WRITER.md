# PocketBook SDIC Writer Plan

## Objective

Add **write support** for PocketBook SDIC (`.dic`) output to PyGlossary, using the Go implementation in `/srv/storage/devcontainers/pbdt/pkg/pocketbook` as the format reference and treating the old `packer.py` there as historical guidance only.

## What Adding A New Output Format In PyGlossary Involves

PyGlossary output formats are implemented as plugins under `pyglossary/plugins/<plugin_name>/`.

Minimum plugin surface:

- `pyglossary/plugins/<plugin_name>/__init__.py`
  - declares plugin metadata such as `lname`, `name`, `description`, `extensions`, `extensionCreate`, `singleFile`, `kind`, `optionsProp`, and optionally `sortOnWrite` / `sortKeyName`
  - exports `Writer`
- `pyglossary/plugins/<plugin_name>/writer.py`
  - typically provides `__init__(glos)`, `open(filename)`, `write()` as a generator, and `finish()`

PyGlossary discovers plugins automatically from `pyglossary/plugins/` via `PluginHandler`, then derives output detection, write options, and format listings from plugin metadata.

Generated artifacts also matter:

- `doc/p/*.md` is generated from plugin metadata
- `plugins-meta/index.json` is generated from plugin metadata
- `README.md` has a hand-maintained supported-formats table and should be updated manually

That means adding a writer is not only code in one file; it also affects generated docs, plugin metadata, tests, and the format list in the repository documentation.

## SDIC Format Constraints From The Reference Implementation

Reference files reviewed:

- `/srv/storage/devcontainers/pbdt/pkg/pocketbook/dictionary.go`
- `/srv/storage/devcontainers/pbdt/pkg/pocketbook/packer.go`
- `/srv/storage/devcontainers/pbdt/pkg/pocketbook/body.go`
- `/srv/storage/devcontainers/pbdt/pkg/pocketbook/metadata.go`
- `/srv/storage/devcontainers/pbdt/pkg/pocketbook/*_test.go`
- `/srv/storage/devcontainers/pbdt/SDIC_METADATA.md`

Key constraints to preserve in the PyGlossary writer:

- Header is 128 bytes with signature `SDIC` and version `0x101`
- Required sections are, in order:
  - collate section
  - morphems section
  - keyboard section
  - sparse index section
  - compressed data blocks
- Dictionary creation requires language metadata files:
  - `collates.txt`
  - `morphems.txt`
  - `keyboard.txt`
- Entry ordering is based on a collated key derived from `collates.txt`, not simple Unicode order
- Data blocks are zlib-compressed and packed with hard limits:
  - max 100 entries per block
  - raw block size must stay below `65531`
  - normal compressed target is below `4097`
  - single oversized entries may need widened single-entry blocks, up to `uint16` size ceiling
- Sparse index entries store:
  - compressed block size as little-endian `uint16`
  - first word in the block as UTF-8 plus NUL terminator
- Entry body semantics should match the Go reference:
  - HTML markup is stored literally
  - literal newlines are removed
  - `<br>` / `<br/>` should be used for visible line breaks instead of raw newlines
  - leading indentation on each line is stripped
  - HTML entities are preserved as-is in written bodies
- The old Python `packer.py` uses legacy inline style-marker bytes for `<b>` / `<i>`; the Go reference does not. The PyGlossary writer should follow the Go behavior, not the old Python packer.

## Design Decisions And Defaults

The following points should be treated as the baseline implementation plan, not as open questions.

1. Plugin naming
   - Recommended module name: `pocketbook_sdic`
   - Recommended display name: `PocketBookSDIC` or `PocketBook SDIC`
   - Recommended extension: `.dic`
   - Because `.dic` is ambiguous across ecosystems, users may often need `--write-format` instead of relying only on extension detection.

2. Duplicate headwords
   - The Go reference merges duplicate words during packing.
   - PyGlossary can emit multiple entries with the same primary term depending on source format.
   - The writer should merge duplicate headwords.
   - Expose a write option such as `merge_duplicates=join|first|error` only if it stays simple.
   - Recommended default: `join`, with a configurable separator.

3. Alternate headwords / synonyms
   - SDIC has no separate synonym table like StarDict.
   - PyGlossary entries may contain alternates in `entry.l_term[1:]`.
   - Do **not** emit duplicate full entries for alternates in the first version.
   - Duplicating every synonym would inflate file size heavily and could work against the original reason those alternates were present.
   - Recommended behavior: ignore alternates for now.
   - If user demand appears later, add an explicit opt-in mode rather than making synonym expansion the default.

4. Binary resource entries
   - SDIC writer has no obvious resource directory equivalent.
   - Recommended behavior: skip `entry.isData()` items.
   - The warning should be aggregated and shown only once, not once per skipped entry.

5. Metadata section at header offset `0x20`
   - The Go writer path reviewed does not populate the optional JSON metadata section.
   - Recommended behavior: omit the optional JSON metadata section entirely.
   - This matches the practical behavior of older tools and avoids complexity for little user value.

6. Metadata defaults and UX
   - Users should get a usable result without hunting for PocketBook language files.
   - Recommended resolution order:
     - explicit write options such as `metadata_dir`, `collates_path`, `keyboard_path`, `morphems_path`
     - default metadata directory `../LanguageFilesPocketbookConverter/en` relative to the PyGlossary checkout during development
     - packaged built-in defaults copied from that repository for installed/runtime use
     - generated minimal fallback data if none of the above are available
   - Do **not** make network download the default runtime behavior in the first version.
   - Automatic download is possible later, but it adds offline, reproducibility, and packaging concerns.
   - Documentation should point users to the LanguageFilesPocketbookConverter repository if they want better language-specific metadata.

7. Morphems defaults
   - `morphems.txt` is not important on modern PocketBook devices because firmware typically has better morphology support already.
   - The writer should therefore accept a minimal default morphems payload.
   - Overriding morphems should remain possible, but this is an advanced option rather than a required setup step.

8. Keyboard defaults
   - English keyboard data is a reasonable default.
   - Users must still be able to override it, especially for Cyrillic-heavy languages common on PocketBook devices in Eastern Europe.
   - This should be called out in user-facing documentation and plugin write options.

9. Sorting behavior
   - PyGlossary does **not** apply locale collation by default.
   - Its default sort key is `headword_lower`, which means lowercased headword plus plain UTF-8/code-point order.
   - Locale-aware sorting exists only when the user explicitly requests a locale sort key such as `headword_lower:es` and has PyICU available.
   - For SDIC, exact reproduction of arbitrary ICU collation in `collates.txt` is probably not worth the complexity in the first version.
   - Recommended behavior:
     - sort internally inside the writer instead of relying on PyGlossary pre-sort machinery
     - generate a compact collate map on the fly from the characters actually seen in the dictionary keys
     - make that generated collate map approximate PyGlossary's default `headword_lower` behavior
     - optionally layer simple accent folding / special-character stripping on top for better lookup ergonomics
   - If a user later requests stricter locale-specific ordering, that should be a separate explicit enhancement.

## Implementation Plan

### Phase 1: Finalize Behavior And Test Strategy

1. Confirm plugin naming and option names.
2. Lock in duplicate-headword merge behavior and synonym-skipping behavior.
3. Lock in the default metadata resolution order and built-in fallback assets.
4. Pick deterministic test fixtures for `collates.txt`, `morphems.txt`, and `keyboard.txt`.
5. Decide the minimal generated fallback policy for when no external metadata files are present.

### Phase 2: Create The Plugin Skeleton

Add a new plugin package:

- `pyglossary/plugins/pocketbook_sdic/__init__.py`
- `pyglossary/plugins/pocketbook_sdic/writer.py`

Expected metadata in `__init__.py`:

- `enable = True`
- `lname`
- `name`
- `description`
- `extensions = (".dic",)`
- `extensionCreate = ".dic"`
- `singleFile = True`
- `kind = "binary"`
- `optionsProp` for at least:
  - `metadata_dir`
   - `collates_path`
   - `keyboard_path`
   - `morphems_path`
   - duplicate-merge behavior option if adopted
   - merge separator if adopted

Sorting behavior:

- Do not declare `sortOnWrite=ALWAYS` for the first version
- Do not try to force SDIC ordering through an existing PyGlossary sort key
- The writer should handle its own internal sorting and collate generation so that SDIC-specific ordering remains under plugin control

### Phase 3: Implement Metadata Loading Helpers

Inside the writer implementation, add helper logic to:

1. Resolve metadata sources using the default/fallback chain
2. Load and parse `collates.txt`
   - map each source rune to its canonical rune, with empty right-hand side meaning strip
3. Load `morphems.txt`
4. Load `keyboard.txt`
5. Provide built-in defaults for runtime usage when the sibling checkout path is unavailable
6. Validate explicit user-supplied paths and produce actionable error messages

Prefer keeping these helpers inside the plugin package unless they clearly need reuse elsewhere.

Recommended default assets policy:

- take `../LanguageFilesPocketbookConverter/en` as the development/reference source
- ship equivalent default assets with the plugin so end users do not need a separate checkout
- keep keyboard override easy and well documented
- allow morphems override, but use a minimal default without making it a blocker

### Phase 4: Implement SDIC Entry Normalization

Writer-side normalization should:

1. Skip data/resource entries with a single aggregated warning.
2. Use only the primary term in the first version.
3. Ignore alternates/synonyms intentionally.
4. Normalize the definition body to match the Go reference behavior:
   - strip leading indentation from each line
   - remove literal newlines
   - preserve HTML tags and entities verbatim
5. Encode each entry payload as:
   - entry size (`uint16`, little-endian)
   - UTF-8 headword plus NUL
   - body with leading `0x20` and trailing `0x20 0x0A 0x00`
6. Track the largest raw entry payload for the header `MaxEntrySize` field.

### Phase 5: Implement Collated Ordering And Merge Logic

1. Compute a collated sort key internally inside the writer.
2. Make the default behavior approximate PyGlossary's `headword_lower` semantics:
   - lowercase headword
   - code-point / UTF-8 order by default
   - optional accent folding / stripping for improved PocketBook lookup behavior
3. Generate a compact collate map from the actual characters present in the glossary instead of requiring a giant universal table.
4. When explicit metadata files are supplied, prefer them over generated defaults.
5. Sort by:
   - collated key first
   - raw word second for deterministic ordering
6. Apply duplicate-word merge behavior.
7. Make output deterministic across runs.

This part is where most format-specific correctness lives; it should be separated enough to unit test directly.

Note on feasibility:

- Matching arbitrary ICU locale sort keys exactly through SDIC `collates.txt` is possible in theory but is not a good first target.
- Matching PyGlossary's default non-locale sorting is straightforward and should be the first goal.

### Phase 6: Implement Section Writers

Implement the mandatory SDIC sections in the same layout as the Go reference:

1. Collate section
   - `uint32` byte length prefix
   - sorted `(input_rune, canonical_rune)` pairs as little-endian `uint16`
2. Morphems section
   - transform lines according to collate mapping
   - encode UTF-16LE with NUL separators and terminal NUL
   - zlib-compress
   - allow a minimal default payload because modern devices mostly ignore this data
3. Keyboard section
   - raw keyboard bytes
   - zlib-compress
   - default to English keyboard data
   - allow explicit override for non-Latin and regional keyboards
4. Sparse index section
   - repeated `uint16 compressed_block_size + first_word + NUL`
   - zlib-compress
5. Data blocks
   - zlib-compressed concatenated entry payloads
   - enforce SDIC block limits

### Phase 7: Implement Block Packing

Implement the same packing rules used by the Go reference:

1. Maximum 100 entries per block.
2. Raw batch size must remain below `65531` after appending the `0x00 0x00` trailer.
3. Normal compressed size target is below `4097`.
4. Use binary search to find the largest batch that fits.
5. If a single entry exceeds the normal compressed target but still fits the `uint16` limit, place it alone in a widened block.
6. Raise a clear error if even a single-entry block exceeds the format ceiling.

This should be factored so it can be unit-tested independently from the plugin wrapper.

### Phase 8: Write Header And Final File

1. Build the 128-byte SDIC header.
2. Write section offsets in the order expected by the format.
3. Store the dictionary display name in the 64-byte header field.
4. Write all sections in sequence.
5. Ensure little-endian integer encoding everywhere.
6. Keep output deterministic.

### Phase 9: Documentation Updates

1. Add plugin metadata with useful `description`, `website`, and `wiki` fields.
2. Run `./scripts/gen` to regenerate:
   - `doc/p/pocketbook_sdic.md`
   - `plugins-meta/index.json`
3. Update `README.md`:
   - add PocketBook SDIC to the supported formats table
   - explain that writing works out of the box with built-in defaults
   - mention that users can improve keyboard and collation behavior by supplying custom metadata files
   - point to the LanguageFilesPocketbookConverter repository for better language-specific files
   - call out output-only support
4. If the generated plugin doc is not enough, add a manual document under `doc/` describing how to source or prepare language metadata files.

### Phase 10: Unit Tests

Add focused unit tests for the SDIC-specific logic. Recommended coverage:

1. `collates.txt` parsing
   - canonical mapping
   - stripping behavior for empty right-hand side
2. Collated-key generation
   - case folding / canonicalization behavior
   - whitespace removal when mapping says to strip
   - generated compact collate map from observed characters
   - approximation of `headword_lower` default behavior
3. Body normalization
   - literal newlines removed
   - indentation removed
   - HTML tags preserved
   - HTML entities preserved
4. Morphems transformation
   - comments and blank lines ignored
   - output encoded as expected
5. Collate section encoding
6. Sparse index encoding
7. Block packing
   - normal multi-entry blocks
   - max-100-items enforcement
   - raw-size limit enforcement
   - widened single-entry fallback
   - hard failure for truly oversized entries
8. Header encoding
   - offsets are correct
   - `EntryCount` and `MaxEntrySize` are correct
9. Aggregated warnings
   - data/resource entries produce one warning, not one warning per entry
10. Metadata resolution
   - explicit override paths win
   - default metadata path works when present
   - packaged fallback works when sibling checkout path is missing

Recommended location:

- `tests/pocketbook_sdic_test.py` for format-specific pure unit tests, or
- `tests/<helper>_test.py` if helper code is factored into separate modules

### Phase 11: Integration Tests

Add end-to-end conversion tests in the existing unittest style, modeled after `g_quickdic6_test.py` and `g_stardict_test.py`.

Recommended tests:

1. `txt -> sdic` golden-file test with a small fixture and deterministic metadata files
2. `txt -> sdic` with alternates to verify that synonyms are skipped by default
3. `txt -> sdic` with duplicate words to verify merge behavior
4. `txt -> sdic` with HTML definitions containing `<b>`, `<i>`, `<br>`, entities, and literal newlines
5. `txt -> sdic` with non-ASCII headwords and collate rules
6. `txt -> sdic` using default built-in metadata without any explicit options
7. keyboard override test for a non-English metadata directory or fixture
8. Oversized-entry failure test

Recommended structure:

- add a new conversion test such as `tests/g_pocketbook_sdic_test.py`
- commit tiny deterministic metadata fixtures under the repository test data path, or add them to the external test-data repo if that is the established pattern for binary fixtures

### Phase 12: Validation Against The Reference Implementation

Before merging, validate the Python writer output against the Go reference behavior.

Suggested validation steps:

1. Generate the same `.dic` from a small XDXF or TXT-derived dataset using both implementations.
2. Compare:
   - header values
   - section offsets
   - sparse index content after decompression
   - decompressed data block contents
3. If byte-for-byte equality is not realistic because of compression implementation differences, compare decompressed semantic sections instead.
4. Smoke-test the produced file with the Go toolkit commands such as `extract-meta`, `lookup`, or `show` if available in the local environment.

## Concrete File Checklist

Expected new or changed files:

- new: `pyglossary/plugins/pocketbook_sdic/__init__.py`
- new: `pyglossary/plugins/pocketbook_sdic/writer.py`
- new: packaged default metadata assets for SDIC fallback behavior
- new: one or more tests for helper logic
- new: `tests/g_pocketbook_sdic_test.py`
- generated: `doc/p/pocketbook_sdic.md`
- generated: `plugins-meta/index.json`
- updated: `README.md`

Potential optional additions:

- helper module if block-packing or metadata parsing becomes too large for `writer.py`
- manual documentation under `doc/`

## Risks And Failure Modes To Watch

1. `.dic` extension ambiguity may make auto-detection unreliable.
2. Exact locale-aware ordering is much harder than matching PyGlossary's default lowercase-headword sort.
3. Incorrect collate handling will produce dictionaries that look valid but have broken lookup order on-device.
4. Newline and entity handling must follow the Go reference, not the older Python packer.
5. Binary golden tests may become brittle if they assert compressed bytes instead of semantic section content.
6. Bundled defaults must be good enough to make the feature usable without setup, but simple enough to maintain.

## Recommended Delivery Order

1. Finalize built-in metadata defaults and path-resolution behavior.
2. Build collate-generation, metadata-loading, and warning-aggregation helpers with unit tests.
3. Implement the plugin wrapper around those helpers.
4. Add integration tests, including zero-configuration conversion.
5. Regenerate docs and plugin metadata.
6. Update `README.md` with override guidance and external metadata source information.
7. Validate output against the Go reference toolkit.
