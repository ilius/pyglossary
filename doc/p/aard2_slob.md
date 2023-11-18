## Aard 2 (.slob)

### General Information

| Attribute       | Value                                                    |
| --------------- | -------------------------------------------------------- |
| Name            | Aard2Slob                                                |
| snake_case_name | aard2_slob                                               |
| Description     | Aard 2 (.slob)                                           |
| Extensions      | `.slob`                                                  |
| Read support    | Yes                                                      |
| Write support   | Yes                                                      |
| Single-file     | Yes                                                      |
| Kind            | 🔢 binary                                                 |
| Sort-on-write   | default_no                                               |
| Sort key        | (`headword_lower`)                                       |
| Wiki            | [@itkach/slob/wiki](https://github.com/itkach/slob/wiki) |
| Website         | [aarddict.org](http://aarddict.org/)                     |

### Write options

| Name                               | Default | Type | Comment                                                         |
| ---------------------------------- | ------- | ---- | --------------------------------------------------------------- |
| compression                        | `zlib`  | str  | Compression Algorithm                                           |
| content_type                       |         | str  | Content Type                                                    |
| file_size_approx                   | `0`     | int  | split up by given approximate file size<br />examples: 100m, 1g |
| file_size_approx_check_num_entries | `100`   | int  | for file_size_approx, check every `[?]` entries                 |
| separate_alternates                | `False` | bool | add alternate headwords as separate entries to slob             |
| word_title                         | `False` | bool | add headwords title to beginning of definition                  |
| version_info                       | `False` | bool | add version info tags to slob file                              |
| audio_goldendict                   | `False` | bool | Convert audio links for GoldenDict (desktop)                    |

### Dependencies for reading and writing

PyPI Links: [PyICU](https://pypi.org/project/PyICU)

To install, run:

```sh
pip3 install PyICU
```

### PyICU

See [doc/pyicu.md](../pyicu.md) file for more detailed instructions on how to install PyICU.

### Dictionary Applications/Tools

| Name & Website                             | Source code                                                      | License | Platforms | Language |
| ------------------------------------------ | ---------------------------------------------------------------- | ------- | --------- | -------- |
| [Aard 2 for Android](http://aarddict.org/) | [@itkach/aard2-android](https://github.com/itkach/aard2-android) | GPL     | Android   | Java     |
| [Aard2 for Web](http://aarddict.org/)      | [@itkach/aard2-web](https://github.com/itkach/aard2-web)         | MPL     | Web       | Java     |
