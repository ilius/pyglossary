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
| Sort-on-write   | always                                               |
| Sort key        | `stardict`                                           |
| Wiki            | [StarDict](https://en.wikipedia.org/wiki/StarDict)   |
| Website         | [huzheng.org/stardict](http://huzheng.org/stardict/) |

### Write options

| Name             | Default | Type | Comment                                                                  |
| ---------------- | ------- | ---- | ------------------------------------------------------------------------ |
| large_file       | `False` | bool | Use idxoffsetbits=64 bits, for large files only                          |
| dictzip          | `True`  | bool | Compress .dict file to .dict.dz                                          |
| sametypesequence |         | str  | Definition format: h=html, m=plaintext, x=xdxf                           |
| audio_icon       | `True`  | bool | Add glossary's audio icon                                                |
| sqlite           | `None`  | bool | Use SQLite to limit memory usage. Default depends on global SQLite mode. |
