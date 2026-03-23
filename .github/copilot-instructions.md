# PyGlossary Repository Instructions

## Scope

These instructions apply to the whole repository.

## Repository Conventions

- Use Python 3.11-compatible code.
- Match the repository's formatting conventions:
  - tabs for indentation in Python files
  - line length around 90 characters
- Keep changes narrowly scoped. Do not reformat unrelated files.
- Preserve existing public APIs unless the task explicitly requires changing them.

## Plugin Work

- Format support lives under `pyglossary/plugins/`.
- Each plugin is typically a package with metadata in `__init__.py` and logic in `reader.py` and/or `writer.py`.
- Output plugins usually expose a `Writer` class with:
  - `__init__(glos)`
  - `open(filename)`
  - `write()` as a generator that receives entries via `yield`
  - `finish()`
- Plugin metadata in `__init__.py` drives format discovery, docs generation, and write-option exposure.
- When adding or changing plugin metadata, also regenerate repository metadata with `./scripts/gen`.

## Documentation Rules

- Files under `doc/p/` are generated from plugin metadata. Do not hand-edit them.
- To update plugin docs and `plugins-meta/index.json`, run `./scripts/gen`.
- `README.md` is not generated. If a format is added or removed, update the supported-formats table manually.

## Testing Conventions

- Tests are `unittest`-based.
- Shared conversion helpers live in `tests/glossary_v2_test.py`.
- For a new format plugin:
  - add focused unit tests for helper logic
  - add end-to-end conversion tests modeled after existing `tests/g_*_test.py` files
- Prefer deterministic fixtures and targeted test runs over broad, expensive runs.
- When testing a writer plugin, cover both successful conversion and failure paths for invalid options or malformed input.

## PyGlossary-Specific Expectations

- Respect `entry.isData()` explicitly in writers.
- Do not assume output formats can store binary resources; warn and skip when necessary.
- If a format requires its own ordering or packing rules, implement them inside the plugin instead of forcing unrelated global behavior.
- Keep writer output deterministic so binary or checksum-based tests remain stable.
- Reuse existing plugin patterns before inventing new abstractions.

## Practical Workflow

- Search first for a similar plugin before implementing a new one.
- For binary writers, study both a minimal plugin and the closest existing complex writer.
- After changing plugin metadata or docs-related fields:
  - run `./scripts/gen`
  - run the relevant targeted tests
- Prefer small helper functions for binary encoding, sorting, and normalization so they can be unit tested directly.

## Avoid

- Do not hand-edit generated files in `doc/p/` without regenerating them from source.
- Do not introduce large framework-style abstractions for a single plugin.
- Do not change unrelated tests or fixtures just to make a new plugin pass.
