## Kobo E-Reader Dictfile (.df)

### General Information

| Attribute       | Value                                                                       |
| --------------- | --------------------------------------------------------------------------- |
| Name            | Dictfile                                                                    |
| snake_case_name | kobo_dictfile                                                               |
| Description     | Kobo E-Reader Dictfile (.df)                                                |
| Extensions      | `.df`                                                                       |
| Read support    | Yes                                                                         |
| Write support   | Yes                                                                         |
| Single-file     | No                                                                          |
| Kind            | 📝 text                                                                      |
| Sort-on-write   | default_no                                                                  |
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

PyPI Links: [mistune 3.0.1](https://pypi.org/project/mistune/3.0.1)

To install, run:

```sh
pip3 install mistune==3.0.1
```

### Dictionary Applications/Tools

| Name & Website                                   | Source code | License | Platforms           | Language |
| ------------------------------------------------ | ----------- | ------- | ------------------- | -------- |
| [dictgen](https://pgaskin.net/dictutil/dictgen/) | ―           | MIT     | Linux, Windows, Mac |          |
