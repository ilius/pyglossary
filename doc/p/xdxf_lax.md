## XDXF Lax (.xdxf)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/xdxf_lax/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute | Value |
| --------- | ----- |
| Name | XdxfLax |
| snake_case_name | xdxf_lax |
| Description | XDXF Lax (.xdxf) |
| Extensions |  |
| Read support | Yes |
| Write support | No |
| Single-file | Yes |
| Kind | 📝 text |
| Wiki | [XDXF](https://en.wikipedia.org/wiki/XDXF) |
| Website | [XDXF standard - @soshial/xdxf_makedict](https://github.com/soshial/xdxf_makedict/tree/master/format_standard) |

### Read options

| Name | Default | Type | Comment |
| ---- | ------- | ---- | ------- |
| html | `True` | bool | Entries are HTML |
| xsl | `False` | bool | Use XSL transformation |
| auto_rtl | `True` | bool | Auto-detect and mark Right-to-Left text |
| example_padding | `10` | int | Padding for examples (in px) |
| word_title | `False` | bool | Add headwords title to beginning of definition |
| pron_color | `gray` | str | Pronunciation color |
| gram_color | `green` | str | Grammar color |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml)

To install, run:

```sh
pip3 install lxml
```

### Related Formats

- [XDXF (.xdxf)](./xdxf.md)
- [XDXF with CSS and JS](./xdxf_css.md)
