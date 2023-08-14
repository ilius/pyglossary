## HTML Directory

### General Information

| Attribute       | Value              |
| --------------- | ------------------ |
| Name            | HtmlDir            |
| snake_case_name | html_dir           |
| Description     | HTML Directory     |
| Extensions      | `.hdir`            |
| Read support    | No                 |
| Write support   | Yes                |
| Single-file     | No                 |
| Kind            | 📁 directory        |
| Sort-on-write   | default_no         |
| Sort key        | (`headword_lower`) |
| Wiki            | ―                  |
| Website         | ―                  |

### Write options

| Name            | Default        | Type | Comment                                        |
| --------------- | -------------- | ---- | ---------------------------------------------- |
| encoding        | `utf-8`        | str  | Encoding/charset                               |
| resources       | `True`         | bool | Enable resources / data files                  |
| max_file_size   | `102400`       | int  | Maximum file size in bytes                     |
| filename_format | `{n:05d}.html` | str  | Filename format, default: {n:05d}.html         |
| escape_defi     | `False`        | bool | Escape definitions                             |
| dark            | `True`         | bool | Use dark style                                 |
| css             |                | str  | Path to css file                               |
| word_title      | `True`         | bool | Add headwords title to beginning of definition |
