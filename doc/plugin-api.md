# Third-party plugin API

This page defines which `pyglossary` modules may be imported by third-party
plugins: plugins that are **not maintained in this repository**, including
forks, separately distributed plugins, and user plugins placed in the
[user plugins directory](../README.md#user-plugins).

Repo-maintained plugins may import internal modules and helpers because they
are updated together with the rest of the code. Third-party plugins should not
do that. Depend only on the modules listed below so that PyGlossary internals
can be refactored without breaking your plugin.

The rules below apply to **direct imports** in third-party plugin code. They do
not restrict transitive imports made internally by an allowed module.

## Allowed modules

These modules are the supported public surface for third-party plugins.

| Module | Public names | Purpose |
| ------ | ------------ | ------- |
| `pyglossary` | `Glossary`, `__version__` | Package entry point; `Glossary` is the legacy alias. |
| `pyglossary.glossary` | `Glossary` | Compatibility alias for the legacy glossary API. |
| `pyglossary.glossary_v1` | `Glossary` | Legacy glossary API kept for compatibility. |
| `pyglossary.glossary_v2` | `Glossary`, `GlossaryCommon`, `ConvertArgs`, `Error`, `ReadError`, `WriteError` | Current glossary/conversion API and public exceptions. |
| `pyglossary.entry` | `Entry`, `DataEntry` | Entry and data-entry types passed between readers, filters, and writers. |
| `pyglossary.option` | `Option`, `BoolOption`, `DictOption`, `EncodingOption`, `FileSizeOption`, `FloatOption`, `HtmlColorOption`, `IntOption`, `ListOption`, `NewlineOption`, `StrOption`, `UnicodeErrorsOption`, `optionFromDict` | Option classes used in a plugin's `optionsProp`. |
| `pyglossary.flags` | `ALWAYS`, `DEFAULT_YES`, `DEFAULT_NO`, `INTERNAL`, `NEVER`, `StrWithDesc`, `YesNoAlwaysNever`, `flagsByName` | Values used by the documented `sortOnWrite` plugin metadata. |
| `pyglossary.core` (limited set) | `log`, `pip`, `exc_note`, `trace`, `VERSION`, `isDebug`, `rootDir`, `dataDir`, `appResDir`, `confDir`, `cacheDir`, `pluginsDir`, `userPluginsDir`, `tmpDir`, `homeDir`, `confJsonFile`, `rootConfJsonFile` | Logging, version, dependency-install hints, and read-only path constants. Do not use `checkCreateConfDir` or other setup internals. |
| `pyglossary.info` | `c_name`, `c_sourceLang`, `c_targetLang`, `c_author`, `c_copyright`, `c_publisher`, `c_creationTime`, `infoKeysAliasDict` | Canonical glossary metadata key names. |
| `pyglossary.compress` | `compressionOpen`, `compressionOpenFunc`, `stdCompressions`, `compress`, `uncompress` | Open glossary files with standard compression extensions. |
| `pyglossary.text_reader` | `TextGlossaryReader`, `TextFilePosWrapper`, `nextBlockResultType` | Base class and helpers for tab-separated text readers. |
| `pyglossary.text_writer` | `TextGlossaryWriter`, `writeTxt` | Base class and helper for tab-separated text writers. |
| `pyglossary.langs` | `Lang`, `langDict` | Language codes and names. |
| `pyglossary.langs.writing_system` | `getWritingSystemFromText` | Detect a writing system/script from text. |
| `pyglossary.xdxf.py_transform` | `XdxfTransformer` | XDXF transformation. |
| `pyglossary.xdxf.xsl_transform` | `XslXdxfTransformer` | XSL-based XDXF transformation. |
| `pyglossary.xdxf.css_js_transform` | `XdxfTransformer` | XDXF CSS/JS transformation. |
| `pyglossary.plugin_lib.dictdlib` | `DictDB` | Vendored third-party dictd database support. |
| `pyglossary.plugin_lib.gregorian` | `isLeap`, `to_jd`, `jd_to` | Gregorian calendar and Julian day conversion helpers. |
| `pyglossary.plugin_lib.mutf8` | `encode_modified_utf8`, `safe_decode_modified_utf8` | Vendored third-party modified UTF-8 encode/decode helpers. |
| `pyglossary.plugin_lib.pureSalsa20` | `Salsa20` | Vendored third-party Salsa20 stream cipher. |
| `pyglossary.plugin_lib.readmdict` | `MDD`, `MDX` | Vendored third-party MDict dictionary reader. |
| `pyglossary.plugin_lib.ripemd128` | `ripemd128` | Vendored third-party RIPEMD-128 hash. |
| `pyglossary.repro_zipfile` | `ReproducibleZipFile`, `__version__` | Reproducible ZIP archive writer. |
| `pyglossary.info_writer` | `InfoWriter` | Base writer for `.info` metadata output. |
| `pyglossary.ebook_base` | `EbookWriter` | Base writer for ebook formats. |
| `pyglossary.entry_list` | `EntryList` | In-memory entry storage for sorted output. |
| `pyglossary.sq_entry_list` | `SqEntryList` | SQLite-backed entry storage for sorted output. |
| `pyglossary.sort_keys` | `NamedSortKey`, `LocaleNamedSortKey`, `defaultSortKeyName`, `lookupSortKey`, `namedSortKeyList` | Sort-key registry used by `Glossary`. |
| `pyglossary.stubs.glossary_types` | `EntryType`, `ReaderGlossaryType`, `WriterGlossaryType`, `RawEntryType`, `EntryListType` | Type-checking only. |
| `pyglossary.stubs.lxml_types` | `Element`, `T_htmlfile` | Type-checking only; plugins that use `lxml`. |
| `pyglossary.stubs.icu_types` | `T_Collator`, `T_Locale` | Type-checking only; plugins that use PyICU. |
| `pyglossary.stubs.sort_keys_types` | Sort-key protocol types | Type-checking only; custom sort keys. |
| `pyglossary.stubs.config_types` | Config protocol types | Type-checking only. |
| `pyglossary.stubs.ui_types` | UI protocol types | Type-checking only. |

The `pyglossary.stubs.*` modules are allowed **only for type annotations**. Do
not import them at runtime to use their contents as behavior.

Import the public names listed above rather than reaching into private names
inside those modules. For example, use `pyglossary.entry.Entry`, not an
underscore-prefixed attribute of an entry object.

## Not allowed for third-party plugins

The following modules are internal or are convenience helpers used by
repo-maintained plugins. Their names and behavior may change without notice.

### Generic helpers and utilities

| Module | Notes |
| ------ | ----- |
| `pyglossary.utils.text_utils` | Use standard library string/packing/regex helpers or plugin-local code. |
| `pyglossary.utils.json_utils` | Use `json` from the standard library. |
| `pyglossary.utils.html_utils` | Use `html`, `html.entities`, or plugin-local code. |
| `pyglossary.utils.xml_utils` | Use `xml.sax.saxutils` or plugin-local code. |
| `pyglossary.utils.file_utils` | Use `pathlib`, `os`, or plugin-local code. |
| `pyglossary.utils.os_utils` | Use `os`, `shutil`, `pathlib`, or plugin-local code. |
| `pyglossary.utils.io_utils` | Use `io` or your own null stream objects. |
| `pyglossary.utils.iter_utils` | Use `itertools` or plugin-local code. |
| `pyglossary.utils.queued_iter` | Internal pipeline helper. |
| `pyglossary.utils.image_utils` | Write extraction logic in the plugin if needed. |
| `pyglossary.utils.apple_utils` | Apple Dictionary-specific helper used by a repo plugin. |
| `pyglossary.langs.persian_utils` | Language-specific helper used by repo plugins. |

### Internal conversion machinery

| Module | Notes |
| ------ | ----- |
| `pyglossary.entry_base` | Use `Entry` and `DataEntry` from `pyglossary.entry` instead. |
| `pyglossary.entry_filters` | Filter pipeline is installed by `Glossary`; plugins must not import it. |
| `pyglossary.entry_merge` | Merge implementation used by the filter pipeline. |
| `pyglossary.glossary_utils` | Use `Error`, `ReadError`, and `WriteError` from `pyglossary.glossary_v2` instead. |
| `pyglossary.exp.glossary_creator` | Host-program API for building glossaries; not a plugin API. |
| `pyglossary.glossary_info` | Metadata mixin mixed into `Glossary`. |
| `pyglossary.glossary_progress` | Progress mixin mixed into `Glossary`. |
| `pyglossary.plugin_handler` | Plugin discovery/loading internals. |
| `pyglossary.plugin_prop` | Plugin metadata/validation internals. |
| `pyglossary.sort_modules` | Built-in sort-key implementations. |
| `pyglossary.logger` | Use `pyglossary.core.log` instead. |
| `pyglossary.core_test` | Test-only helpers. |

### Applications and experiments

| Module | Notes |
| ------ | ----- |
| `pyglossary.ui` | UI/front-end implementation; plugins do not need it. |
| `pyglossary.exp` | Experimental code, not part of the plugin API. |

## Notes for plugin authors

- If a helper is missing from this list, implement the small amount of logic in
  your plugin or add a dependency to the original package instead of importing
  a PyGlossary internal module.
- If you fork a repo-maintained plugin, keep its internal imports only if you
  also vendor the PyGlossary modules it depends on, or update it to use the
  allowed API above.
- Type annotations using `pyglossary.stubs.*` are only meaningful while
  type-checking. Do not use these modules at runtime for behavior.
