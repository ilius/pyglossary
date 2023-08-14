## JMDict

### General Information

| Attribute       | Value                                                            |
| --------------- | ---------------------------------------------------------------- |
| Name            | JMDict                                                           |
| snake_case_name | jmdict                                                           |
| Description     | JMDict                                                           |
| Extensions      |                                                                  |
| Read support    | Yes                                                              |
| Write support   | No                                                               |
| Single-file     | Yes                                                              |
| Kind            | 📝 text                                                           |
| Sort-on-write   | default_no                                                       |
| Sort key        | (`headword_lower`)                                               |
| Wiki            | [JMdict](https://en.wikipedia.org/wiki/JMdict)                   |
| Website         | [The JMDict Project](https://www.edrdg.org/jmdict/j_jmdict.html) |

### Read options

| Name            | Default | Type | Comment                                |
| --------------- | ------- | ---- | -------------------------------------- |
| example_padding | `10`    | int  | Padding for examples (in px)           |
| example_color   |         | str  | Examples color                         |
| translitation   | `False` | bool | Add translitation (romaji) of keywords |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml)

To install, run:

```sh
pip3 install lxml
```
