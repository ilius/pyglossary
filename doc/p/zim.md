## Zim (.zim, for Kiwix)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/zim/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute | Value |
| --------- | ----- |
| Name | Zim |
| snake_case_name | zim |
| Description | Zim (.zim, for Kiwix) |
| Extensions | `.zim` |
| Read support | Yes |
| Write support | Yes |
| Single-file | Yes |
| Kind | 🔢 binary |
| Sort-on-write | Internal (format-defined order, --sort is ignored) |
| Sort key | (format-defined order) |
| Wiki | [ZIM (file format)](<https://en.wikipedia.org/wiki/ZIM_(file_format)>) |
| Website | [OpenZIM](https://wiki.openzim.org/wiki/OpenZIM) |

### Read options

| Name | Default | Type | Comment |
| ---- | ------- | ---- | ------- |
| text_unicode_errors | `replace` | str | Unicode Errors for plaintext, values: `strict`, `ignore`, `replace` |
| html_unicode_errors | `replace` | str | Unicode Errors for HTML, values: `strict`, `ignore`, `replace` |

### Write options

| Name | Default | Type | Comment |
| ---- | ------- | ---- | ------- |
| compress | `True` | bool | Compress ZIM content (zstd) |
| indexing | `True` | bool | Build the ZIM full-text/index metadata |
| language |  | str | ZIM language code (ISO 639-3), overrides glossary source language |
| word_title | `False` | bool | Add headword title to beginning of definition |
| front_article | `True` | bool | Include entries in random and suggestion indices |
| verbose | `False` | bool | Enable verbose output from libzim |

### Dependencies for reading and writing

PyPI Links: [libzim>=4.0](https://pypi.org/project/libzim%3E=4.0)

To install, run:

```sh
pip3 install libzim>=4.0
```

### Sorting

Entries are always stored in libzim's order: `A/` followed by the percent-encoded
headword, compared byte by byte. `--sort` and `--sort-key` do not change the output.
Duplicate headwords are stored as `A/word_2`, `A/word_3`, and so on, and aliases
(`word|alias`) are read back as separate entries. The order after a round trip can
therefore differ from the source order.

### Dictionary Applications/Tools

| Name & Website | Source code | License | Platforms | Language |
| -------------- | ----------- | ------- | --------- | -------- |
| [Kiwix Desktop](https://github.com/kiwix/kiwix-desktop) | ― | GPL | Linux, Windows |  |
| [Kiwix JS](https://github.com/kiwix/kiwix-js) | ― | GPL | Windows |  |
| [Kiwix Serve](https://github.com/kiwix/kiwix-tools) | ― | GPL | Linux, Windows |  |
| [Kiwix for Apple Mac OS X](macos.kiwix.org) | ― |  | Mac |  |
| [Kiwix for Android](https://github.com/kiwix/kiwix-android) | ― | GPL | Android |  |

### Related Formats

- [Aard 2 (.slob)](./aard2_slob.md)
