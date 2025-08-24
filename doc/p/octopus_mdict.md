## Octopus MDict (.mdx)

### General Information

| Attribute       | Value                                                                |
| --------------- | -------------------------------------------------------------------- |
| Name            | OctopusMdict                                                         |
| snake_case_name | octopus_mdict                                                        |
| Description     | Octopus MDict (.mdx)                                                 |
| Extensions      | `.mdx`                                                               |
| Read support    | Yes                                                                  |
| Write support   | No                                                                   |
| Single-file     | No                                                                   |
| Kind            | 🔢 binary                                                             |
| Wiki            | ―                                                                    |
| Website         | [Download - MDict.cn](https://www.mdict.cn/wp/?page_id=5325&lang=en) |

### Read options

| Name                | Default | Type | Comment                             |
| ------------------- | ------- | ---- | ----------------------------------- |
| encoding            |         | str  | Encoding/charset                    |
| substyle            | `True`  | bool | Enable substyle                     |
| same_dir_data_files | `False` | bool | Read data files from same directory |
| audio               | `False` | bool | Enable audio objects                |

### Dependencies for reading

PyPI Links: [xxhash](https://pypi.org/project/xxhash)

To install, run:

```sh
pip3 install xxhash
```

### `python-lzo` is required for **some** MDX glossaries.

First try converting your MDX file, if failed (`AssertionError` probably),
then try to install [LZO library and Python binding](../lzo.md).

### Dictionary Applications/Tools

| Name & Website                 | Source code | License     | Platforms                  | Language |
| ------------------------------ | ----------- | ----------- | -------------------------- | -------- |
| [MDict](https://www.mdict.cn/) | ―           | Proprietary | Android, iOS, Windows, Mac |          |
