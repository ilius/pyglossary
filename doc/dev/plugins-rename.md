# Plugin directory renames

These are the plugins whose directory name differs from `lname`, with the
implications of renaming each directory to match `lname`.

The core constraint is in `PluginLoader.loadPlugins`: it adds
`pyglossary/plugins` to `sys.path` and imports each plugin by its **bare**
top-level module name (`__import__("csv")`, not
`pyglossary.plugins.csv`). `sys.path.append` puts the plugin directory after
the standard library and site-packages. Therefore a directory named after an
already importable top-level module can be skipped silently. This matters most
for `csv` and `json`.

This also affects scripts that call `Glossary.init(usePluginsJson=False)`
(`scripts/gen`, `scripts/plugin-validate.py`, `scripts/pyproject-validate.py`):
they rely entirely on the bare-name directory scan, so a conflicting directory
name can remove the plugin from generated metadata and validation.

Every rename still needs `./scripts/gen`, removal of stale `__pycache__`, and
the normal test/Ruff pass. The sections below list what is specific to each
case.

| Directory | `lname` | Main risk |
| --------- | ------- | --------- |
| `xliff_plugin` | `xliff` | No known stdlib/PyPI conflict; generic name |
| `csv_plugin` | `csv` | Standard-library `csv` conflict; cannot be loaded by the directory scan |
| `json_plugin` | `json` | Standard-library `json` conflict; cannot be loaded by the directory scan |
| `ebook_epub2` | `epub2` | No known stdlib/PyPI conflict; low risk |
| `ebook_kobo` | `kobo` | PyPI `kobo` package conflict; tests import the old path |
| `ebook_kobo_dictfile` | `kobo_dictfile` | No known stdlib/PyPI conflict; low risk |
| `ebook_mobi` | `mobi` | PyPI `mobi` package conflict |
| `info_plugin` | `info` | Generic top-level name; possible user-plugin/package collision |
| `tmx_plugin` | `tmx` | PyPI `tmx` package conflict |
| `wordfrequency_info` | `wordfrequency` | PyPI `wordfrequency` package conflict; Ruff per-file ignore path |

## `csv_plugin` -> `csv`

**Do not rename under the current loader.**

- `csv` is a standard-library module, so `__import__("csv")` during the
  directory scan returns the stdlib module, which has no `lname`, `Reader`, or
  `Writer`. The plugin is skipped. `sys.modules` may already contain `csv`
  anyway.
- `scripts/gen` uses `usePluginsJson=False`, so the plugin would disappear from
  `plugins-meta/index.json` and `doc/p/csv.md`.
- The plugin imports `csv` in `__init__.py`, `reader.py`, and `writer.py`. If
  the plugin directory were ever placed before the standard library on
  `sys.path` and loaded under the bare name `csv`, those imports would resolve
  to the plugin itself instead of the stdlib.
- Repository links use the directory name: `README.md`, `ARCHITECTURE.md`, and
  `CONTRIBUTING.md` all point to `pyglossary/plugins/csv_plugin/`.
- Tests use the format name (`CSV`), so `tests/g_csv_plugin_test.py` would not
  need renaming.

If this rename is required, first change plugin loading to always use
fully-qualified package imports (`pyglossary.plugins.<module>`), then keep the
stdlib imports explicit and rerun all `usePluginsJson=False` validation.

## `json_plugin` -> `json`

**Do not rename under the current loader.**

- `json` is a standard-library module. `PluginHandler.loadPluginsFromJson`
  itself imports `json`, so `sys.modules["json"]` is already the stdlib module.
  The bare-name directory scan cannot load this plugin.
- `scripts/gen` would drop the plugin from the generated index and docs.
- `writer.py` uses `from json import dumps`; if the plugin directory ever
  shadowed the stdlib under the bare name `json`, that import would recurse
  into the plugin.
- `doc/releases/4.0.0.md` mentions the historical
  `pyglossary/plugins/json_plugin.py` path, but it is a release-note artifact
  and should not be rewritten.
- Tests use the `Json` format name and do not import the module path.

Same prerequisite as `csv_plugin`: fix the loader to use qualified imports
before considering this rename.

## `ebook_epub2` -> `epub2`

- No standard-library module named `epub2`.
- No PyPI project named `epub2` was found when checking the index; a user
  plugin or private package with that name could still exist, so check
  `~/.pyglossary/plugins` and the target environment.
- No internal imports named `epub2`; the writer only uses `os` and PyGlossary
  helpers.
- No tests or repository links import `pyglossary.plugins.ebook_epub2`.
- `lname` is already `epub2`, so generated docs and `--read-format`/`--output-format`
  names do not change.

Low risk.

## `ebook_kobo` -> `kobo`

- No standard-library module named `kobo`.
- A PyPI project named `kobo` exists (Kobo eReader tooling). If it is installed
  or imported, the bare-name directory scan imports that package instead of
  the plugin and skips the plugin. `scripts/gen` and other
  `usePluginsJson=False` paths are affected.
- Two tests import the module path directly and must be updated:
  `tests/ebook_kobo_test.py` and `tests/unused_test.py`.
- No internal imports named `kobo`; `writer.py` only calls `log.info(...)`.
- `lname` is already `kobo`, so format names and generated docs do not change.

Rename only after deciding that the top-level name `kobo` is acceptable and
updating the direct test imports.

## `ebook_kobo_dictfile` -> `kobo_dictfile`

- No standard-library module and no PyPI project named `kobo_dictfile` was
  found; a user plugin could still use the name.
- No internal imports named `kobo_dictfile`.
- No direct repository or test imports use the old path; tests use the
  `Dictfile` format name.
- `lname` is already `kobo_dictfile`, so docs and CLI format names are
  unaffected.

Low risk.

## `ebook_mobi` -> `mobi`

- No standard-library module named `mobi`.
- A PyPI project named `mobi` exists. If installed, the bare-name directory
  scan imports that package and skips the plugin, including in
  `scripts/gen`/validation runs.
- No internal imports named `mobi`; `writer.py` only calls `log.info(...)`.
- No tests import `pyglossary.plugins.ebook_mobi`; tests use the `Mobi` format
  name.
- `lname` is already `mobi`, so docs and CLI format names are unaffected.

Rename only if the environment is not expected to have the PyPI `mobi`
package, or after fixing the loader to use qualified imports.

## `info_plugin` -> `info`

- No standard-library module named `info`. The existing `pyglossary.info`
  package is a subpackage, not a top-level `info` module, so it does not
  conflict with the bare-name scan.
- No PyPI project named `info` was found, but `info` is a very generic
  top-level name and is a plausible user-plugin or local package collision.
- Internal imports use `pyglossary.info_writer`, not `info`, so they are not
  affected by the directory rename.
- No tests or repository links import `pyglossary.plugins.info_plugin`; tests
  use the `Info` format name.
- `lname` is already `info`, so docs and CLI format names are unaffected.

Low-to-medium risk, mostly from top-level name collisions outside this
repository.

## `tmx_plugin` -> `tmx`

- No standard-library module named `tmx`.
- A PyPI project named `tmx` exists. If installed, the bare-name directory scan
  imports that package and skips the plugin, including in `scripts/gen` and
  validation scripts.
- No internal imports named `tmx`.
- No tests or repository links import `pyglossary.plugins.tmx_plugin`; the
  format is used as `TMX`.
- `lname` is already `tmx`, so docs and CLI format names are unaffected.

Same caveat as `mobi`/`kobo`.

## `wordfrequency_info` -> `wordfrequency`

- No standard-library module named `wordfrequency`.
- A PyPI project named `wordfrequency` exists (`0.1`). If installed, the
  bare-name directory scan can import that package instead of the plugin and
  skip the plugin in `scripts/gen`/validation.
- `pyproject.toml` has a per-file Ruff ignore keyed to the old path:
  `pyglossary/plugins/wordfrequency_info/reader.py`. Move it to the new path or
  the `E501` suppression silently stops applying.
- No tests or repository links import the old module path; the format is used
  as `WordFrequency`.
- `lname` is already `wordfrequency`, so docs and CLI format names do not
  change.

Rename only after moving the Ruff override and checking for the PyPI package.

## `xliff_plugin` -> `xliff`

- No standard-library module named `xliff`.
- No PyPI project named `xliff` was found; a user plugin or private package
  could still use the name.
- No internal imports named `xliff`.
- No tests or repository links import `pyglossary.plugins.xliff_plugin`; the
  format is used as `XLIFF`.
- `lname` is already `xliff`, so docs and CLI format names are unaffected.

Low risk.

## `octopus_mdict_new` -> `octopus_mdict`

Already completed.

- No standard-library, PyPI, or internal `octopus_mdict` import conflict.
- `plugins-meta/index.json` was regenerated; its `module` changed from
  `octopus_mdict_new` to `octopus_mdict` while `lname` stayed
  `octopus_mdict`.
- No direct tests import the old path.
- `lname` was already `octopus_mdict`, so docs and CLI format names did not
  change.

## Common follow-up for any of these cases

- Remove the old directory remnants (`__pycache__`, generated coverage output)
  after `git mv`.
- Run `./scripts/gen` and commit `plugins-meta/index.json` in the same change.
- Check `scripts/plugin-validate.py` and `scripts/pyproject-validate.py`, which
  load plugins with `usePluginsJson=False`.
- Check `~/.pyglossary/plugins` for a user plugin with the proposed new module
  name. The loader's `loadedModules` set is process-global, and a collision can
  silently skip one of the two plugins.
- Check `pyproject.toml` for per-file Ruff/typing/coverage paths and update
  them.
- Release notes automation compares plugin directories with the previous tag;
  a directory rename looks like a new plugin, so review the generated notes
  manually.
