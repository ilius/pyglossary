## XDXF (.xdxf)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/xdxf/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute | Value |
| --------- | ----- |
| Name | Xdxf |
| snake_case_name | xdxf |
| Description | XDXF (.xdxf) |
| Extensions | `.xdxf` |
| Read support | Yes |
| Write support | Yes |
| Single-file | Yes |
| Kind | 📝 text |
| Sort-on-write | No (by default) |
| Sort key | (`headword_lower`) |
| Wiki | [XDXF](https://en.wikipedia.org/wiki/XDXF) |
| Website | [XDXF standard - @soshial/xdxf_makedict](https://github.com/soshial/xdxf_makedict/tree/master/format_standard) |

### Read options

| Name | Default | Type | Comment |
| ---- | ------- | ---- | ------- |
| html | `True` | bool | Entries are HTML |
| xsl | `False` | bool | Use XSL transformation |
| auto_rtl | `True` | bool | Auto-detect and mark Right-to-Left text |
| example_padding | `10` | int | Padding for examples (in px) |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml)

To install, run:

```sh
pip3 install lxml
```

### Write support

The XDXF writer only writes entries that are already XDXF-formatted, so it is
only useful when reading from StarDict or FreeDict, or when modifying an existing
XDXF glossary.

### Dictionary Applications/Tools

| Name & Website | Source code | License | Platforms | Language |
| -------------- | ----------- | ------- | --------- | -------- |
| [GoldenDict-NG by @xiaoyifang](https://xiaoyifang.github.io/goldendict-ng/) | [@xiaoyifang/goldendict-ng](https://github.com/xiaoyifang/goldendict-ng) | GPL | Linux, Windows, Mac | C++ |
| [GoldenDict](http://goldendict.org/) | [@goldendict/goldendict](https://github.com/goldendict/goldendict) | GPL | Linux, Windows, Mac | C++ |
| [QTranslate](https://qtranslate.en.lo4d.com/windows) | ― | Proprietary (Freeware) | Windows | C++ |
| [Alpus](https://alpusapp.com/) | ― | Proprietary (Freeware) | Windows, Mac, Linux, Android | Java |

### Related Formats

- [XDXF with CSS and JS](./xdxf_css.md)
- [XDXF Lax (.xdxf)](./xdxf_lax.md)
