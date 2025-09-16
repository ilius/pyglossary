## StarDict (Merge Syns)

### General Information

| Attribute       | Value                                                |
| --------------- | ---------------------------------------------------- |
| Name            | StardictMergeSyns                                    |
| snake_case_name | stardict_merge_syns                                  |
| Description     | StarDict (Merge Syns)                                |
| Extensions      |                                                      |
| Read support    | No                                                   |
| Write support   | Yes                                                  |
| Single-file     | No                                                   |
| Kind            | 📁 directory                                          |
| Sort-on-write   | Always                                               |
| Sort key        | `stardict`                                           |
| Wiki            | [StarDict](https://en.wikipedia.org/wiki/StarDict)   |
| Website         | [huzheng.org/stardict](http://huzheng.org/stardict/) |

### Write options

| Name             | Default | Type | Comment                                                                  |
| ---------------- | ------- | ---- | ------------------------------------------------------------------------ |
| large_file       | `False` | bool | Use idxoffsetbits=64 bits, for large files only                          |
| dictzip          | `False` | bool | Compress .dict file to .dict.dz                                          |
| sametypesequence |         | str  | Definition format: h=html, m=plaintext, x=xdxf                           |
| audio_icon       | `True`  | bool | Add glossary's audio icon                                                |
| sqlite           | `None`  | bool | Use SQLite to limit memory usage. Default depends on global SQLite mode. |

### Dictionary Applications/Tools

| Name & Website                                           | Source code                                                | License | Platforms                                                   | Language |
| -------------------------------------------------------- | ---------------------------------------------------------- | ------- | ----------------------------------------------------------- | -------- |
| [KOReader](http://koreader.rocks/)                       | [@koreader/koreader](https://github.com/koreader/koreader) | AGPLv3  | Android, Amazon Kindle, Kobo eReader, PocketBook, Cervantes | Lua      |
| [sdcv (command line)](https://dushistov.github.io/sdcv/) | [@Dushistov/sdcv](https://github.com/Dushistov/sdcv)       | GPLv2   | Linux, Windows, Mac, Android                                | C++      |

### Related Formats

- [StarDict (.ifo)](./stardict.md)
- [StarDict Textual File (.xml)](./stardict_textual.md)
