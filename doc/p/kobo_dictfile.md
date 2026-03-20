## Kobo E-Reader Dictfile (.df)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/kobo_dictfile/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                                                                       |
| --------------- | --------------------------------------------------------------------------- |
| Name            | Dictfile                                                                    |
| snake_case_name | kobo_dictfile                                                               |
| Description     | Kobo E-Reader Dictfile (.df)                                                |
| Extensions      | `.df`                                                                       |
| Read support    | Yes                                                                         |
| Write support   | Yes                                                                         |
| Single-file     | Yes                                                                         |
| Kind            | 📝 text                                                                      |
| Sort-on-write   | No (by default)                                                             |
| Sort key        | (`headword_lower`)                                                          |
| Wiki            | ―                                                                           |
| Website         | [dictgen - dictutil](https://pgaskin.net/dictutil/dictgen/#dictfile-format) |

### Read options

| Name                  | Default | Type | Comment               |
| --------------------- | ------- | ---- | --------------------- |
| encoding              | `utf-8` | str  | Encoding/charset      |
| extract_inline_images | `True`  | bool | Extract inline images |

### Write options

| Name     | Default | Type | Comment          |
| -------- | ------- | ---- | ---------------- |
| encoding | `utf-8` | str  | Encoding/charset |

### Dependencies for reading

PyPI Links: [mistune](https://pypi.org/project/mistune)

To install, run:

```sh
pip3 install mistune
```

### Dictionary Applications/Tools

| Name & Website                                   | Source code | License | Platforms           | Language |
| ------------------------------------------------ | ----------- | ------- | ------------------- | -------- |
| [dictgen](https://pgaskin.net/dictutil/dictgen/) | ―           | MIT     | Linux, Windows, Mac |          |

### Related Formats

- [Kobo E-Reader Dictionary](./kobo.md)
