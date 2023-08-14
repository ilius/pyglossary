## XDXF Lax (.xdxf)

### General Information

| Attribute       | Value                                                                                                          |
| --------------- | -------------------------------------------------------------------------------------------------------------- |
| Name            | XdxfLax                                                                                                        |
| snake_case_name | xdxf_lax                                                                                                       |
| Description     | XDXF Lax (.xdxf)                                                                                               |
| Extensions      |                                                                                                                |
| Read support    | Yes                                                                                                            |
| Write support   | No                                                                                                             |
| Single-file     | Yes                                                                                                            |
| Kind            | 📝 text                                                                                                         |
| Sort-on-write   | default_no                                                                                                     |
| Sort key        | (`headword_lower`)                                                                                             |
| Wiki            | [XDXF](https://en.wikipedia.org/wiki/XDXF)                                                                     |
| Website         | [XDXF standard - @soshial/xdxf_makedict](https://github.com/soshial/xdxf_makedict/tree/master/format_standard) |

### Read options

| Name | Default | Type | Comment                |
| ---- | ------- | ---- | ---------------------- |
| html | `True`  | bool | Entries are HTML       |
| xsl  | `False` | bool | Use XSL transformation |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml)

To install, run:

```sh
pip3 install lxml
```
