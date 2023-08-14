## CC-CEDICT

### General Information

| Attribute       | Value                                                       |
| --------------- | ----------------------------------------------------------- |
| Name            | CC-CEDICT                                                   |
| snake_case_name | cc_cedict                                                   |
| Description     | CC-CEDICT                                                   |
| Extensions      | `.u8`                                                       |
| Read support    | Yes                                                         |
| Write support   | No                                                          |
| Single-file     | Yes                                                         |
| Kind            | 📝 text                                                      |
| Sort-on-write   | default_no                                                  |
| Sort key        | (`headword_lower`)                                          |
| Wiki            | [CEDICT](https://en.wikipedia.org/wiki/CEDICT)              |
| Website         | [CC-CEDICT Editor](https://cc-cedict.org/editor/editor.php) |

### Read options

| Name              | Default | Type | Comment                                       |
| ----------------- | ------- | ---- | --------------------------------------------- |
| encoding          | `utf-8` | str  | Encoding/charset                              |
| traditional_title | `False` | bool | Use traditional Chinese for entry titles/keys |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml)

To install, run:

```sh
pip3 install lxml
```
