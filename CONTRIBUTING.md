# Contributing to PyGlossary

Thank you for considering a contribution. PyGlossary converts dictionary files between many formats; pull requests that fix bugs, improve documentation, or add useful formats and options are welcome.

This guide summarizes how we work in this repository. For user-facing behavior, requirements, and supported formats, start with [README.md](README.md).

## Table of contents

- [Code of conduct](#code-of-conduct)
- [License](#license)
- [What to contribute](#what-to-contribute)
  - [Requesting support for a new format](#requesting-support-for-a-new-format)
- [Development setup](#development-setup)
- [Running tests](#running-tests)
- [Linting and formatting (Ruff)](#linting-and-formatting-ruff)
- [Plugins and generated files](#plugins-and-generated-files)
  - [Plugin metadata used by `./scripts/gen`](#plugin-metadata-used-by-scriptsgen)
- [Architecture and docs for contributors](#architecture-and-docs-for-contributors)
- [Pull request checklist](#pull-request-checklist)
- [Questions](#questions)

## Code of conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Be respectful and assume good intent.

## License

PyGlossary is licensed under [GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0.html). By contributing, you agree that your contributions will be available under the same license.

## What to contribute

- **Bug fixes** with a clear explanation of the problem and how the change fixes it.
- **New or improved format support** via plugins, with documentation and tests where practical.
- **Documentation** corrections or clarifications under `doc/`.
- **Tests** that lock in correct behavior and prevent regressions.

For **feature ideas** (new formats, options, or parameters), open an issue first when the scope is large or unclear. The [feature request template](.github/ISSUE_TEMPLATE/feature-request.md) asks for a problem description, a proposed solution, and format evidence (official links, samples, and similar). That structure speeds up review.

### Requesting support for a new format

To make a new format implementable and testable, please always include:

- **Official references**\
  Link to the **official website** for the format or the **official dictionary / application** that uses it (specification, developer documentation, or the product page—not only a random blog or forum thread). This helps confirm field layout, licensing, and intended behavior.

- **Sample files**\
  Attach small samples to the issue when GitHub allows it, or upload them elsewhere and **paste the download link** in the issue.

  If files are **too large** for GitHub attachments, use **Google Drive**, **OneDrive**, **Dropbox**, **[MEGA](https://mega.io)** or another file host, and share a link that does not require a paid account to download. When possible, prefer services whose **download or sharing pages are available in English** so maintainers can follow the flow without guessing another language’s UI.

  If you cannot share samples (copyright, private data), say so explicitly and describe the structure (headers, encoding, compression) as precisely as you can.

## Development setup

- **Python**: 3.12 or newer (see [README.md](README.md#requirements)).
- **Clone** the repository and use a virtual environment.

```bash
git clone https://github.com/ilius/pyglossary.git
cd pyglossary
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

- **Test dependencies** (matches CI):

```bash
sh ./scripts/test-deps.sh
```

This installs [requirements-test.txt](requirements-test.txt). Many tests also need optional libraries from [requirements.txt](requirements.txt) for specific formats; install those if your change touches those code paths.

- **Run from the repo** without installing the package: use `./main.py` (see [README.md](./README.md)) or add the repo root on `PYTHONPATH`. To install the `pyglossary` entry point into the venv:

```bash
pip install -e .
```

Next steps: [Running tests](#running-tests) and [Linting and formatting (Ruff)](#linting-and-formatting-ruff).

## Running tests

Core and UI tests use the standard library’s `unittest` module.

- **All tests** (from repo root):

```bash
bash scripts/test.sh # main tests: often enough for plugin development
bash scripts/test-deprecated.sh # tests for deprecated Glossary API
bash scripts/test-ui.sh # tests for UI (only run if you changed ui/)
```

- **Single test module** (verbose):

```bash
cd tests
TEST_VERBOSE=1 python -m unittest g_csv_plugin_test.py
```

Some CI jobs set extra environment variables. If a job fails only there, check [.github/workflows/](.github/workflows/).

## Linting and formatting (Ruff)

CI runs Ruff format and Ruff check with fix, then fails if the tree is dirty. Match that locally so your branch stays green.

Install or upgrade Ruff (a local install is often newer than CI and stays compatible), then format and apply safe fixes:

```bash
pip install -U ruff
ruff format
ruff check --fix
```

You can run `ruff check --fix --unsafe-fixes` when you need it; review the resulting diff carefully. Commit or stage your work first so unsafe-fix changes stay easy to pick out in `git diff`.

Project rules live in [pyproject.toml](pyproject.toml) under `[tool.ruff]` (tabs, 90-character lines, Python 3.12 target, and so on).

## Plugins and generated files

When you **add a plugin** or **change plugin metadata or options**, run **`./scripts/gen`** and commit the refreshed tracked files. Typical invocation:

```bash
python -m pip install mako
./scripts/gen
```

That refreshes generated outputs, including [`plugins-meta/index.json`](plugins-meta/index.json) and the per-format pages under [`doc/p/`](doc/p/) (plus other files listed in [`scripts/gen`](scripts/gen)). CI [validates](.github/workflows/validate.yml) that `scripts/plugin-validate.py`, `scripts/pyproject-validate.py`, and `./scripts/gen` produce **no uncommitted diff**.

### Plugin metadata used by `./scripts/gen`

[`scripts/gen.d/plugin-index.py`](scripts/gen.d/plugin-index.py) writes **`plugins-meta/index.json`**. [`scripts/gen.d/plugin-doc.py`](scripts/gen.d/plugin-doc.py) writes **`doc/p/<lname>.md`** per format and **`doc/p/__index__.md`**. Both read the live plugin package (mainly **`__init__.py`** on the module and the **`Reader`** / **`Writer`** classes for options and dependency tables).

Module-level names in **`__init__.py`** that feed those outputs include:

| Name | Role in generated `index.json` or `doc/p/*.md` |
| ---- | ---------------------------------------------- |
| **`enable`** | Whether the plugin is active for format lists. |
| **`lname`** | Internal id; file stem `doc/p/{lname}.md` and `snake_case_name` in the format page. |
| **`name`** | Display name in tables and UI metadata. |
| **`description`** | One-line title (`##` in the format page) and index column text. |
| **`extensions`** | File extensions row. |
| **`extensionCreate`** | Output path hint in the general-info table. |
| **`singleFile`** | Single-file vs multi-file row. |
| **`kind`** | `text` / `binary` / `directory` / `package` (with icon in the doc). |
| **`wiki`**, **`website`** | Links in the format page. |
| **`optionsProp`** | Options serialized into `index.json` and documented in the format page. |
| **`sortOnWrite`**, **`sortKeyName`** | Sort rows when the writer sorts (also in `index.json` when set). |
| **`sortEncoding`** | Used when resolving default sort encoding for a writer (not written into `index.json`). |
| **`relatedFormats`** | **Related formats** links at the bottom of `doc/p/<lname>.md`. |
| **`docTail`** | Extra Markdown inserted into the generated format page. |

These variables are used in the `Glossary` class and in user interfaces, either via `plugins-meta/index.json` or directly from the plugin module.

The purpose of `plugins-meta/index.json` is to avoid loading every plugin module at startup and keep startup fast. In debug/trace mode (`-v4` or `-v5`), all plugin modules are loaded.

**`Reader`** / **`Writer`** (when defined) supply **read/write options** and **PyPI dependency** sections in the generated format page.

Optional **`tools.toml`** next to `__init__.py` (for example [`pyglossary/plugins/stardict/tools.toml`](pyglossary/plugins/stardict/tools.toml)) fills the **Dictionary Applications/Tools** table: each top-level TOML section is one app; common keys are `web`, `source`, `wiki`, `platforms`, `license`, and `plang`. Omit the file if there is nothing to list. Copy an existing plugin’s `tools.toml` as a template.

## Architecture and docs for contributors

| Topic | Document |
| ----- | -------- |
| Entry structure, filters | [doc/internals.md](doc/internals.md), [doc/entry-filters.md](doc/entry-filters.md) |
| Configuration | [doc/config.rst](doc/config.rst) |
| Using PyGlossary from Python | [doc/lib-usage.md](doc/lib-usage.md), [doc/lib-examples/](doc/lib-examples/) |
| Direct / indirect mode, SQLite, sorting | [README.md](README.md) |
| Plugin examples | [pyglossary/plugins/testformat/](pyglossary/plugins/testformat/), [pyglossary/plugins/csv_plugin/](pyglossary/plugins/csv_plugin/) |

The README [Plugin development](README.md#plugin-development) section points to the same examples and the `scripts/gen` step.

## Pull request checklist

Before you open or update a PR:

1. **Tests**: `bash scripts/test.sh` or `bash scripts/test-ui.sh`
1. **Ruff**: `ruff format` and `ruff check --fix` with a clean `git diff`.
1. **Plugins / metadata**: if applicable, `./scripts/gen` and commit the generated changes.
1. **Description**: explain the motivation, what changed, and any trade-offs or limitations. Link related issues when they exist.
1. **Scope**: keep changes focused; unrelated refactors make review harder.

CI overview: [Test](.github/workflows/test.yml), [Ruff](.github/workflows/ruff.yml), [Validate](.github/workflows/validate.yml), and related workflows under [.github/workflows/](.github/workflows/).

## Questions

Use [GitHub Issues](https://github.com/ilius/pyglossary/issues) for bugs, improvements and feature requests. Include version, OS, and exact command or UI steps. For new formats, include official links and samples as described [above](#requesting-support-for-a-new-format).

For general dictionary-related discussions and questions, please use [Discussions](https://github.com/ilius/pyglossary/discussions).
