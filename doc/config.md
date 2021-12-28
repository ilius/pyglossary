## Configuration Parameters

| Name                  | Command Flags                        | Type  | Default   | Comment                                                                               |
| --------------------- | ------------------------------------ | ----- | --------- | ------------------------------------------------------------------------------------- |
| `log_time`            | `--log-time`<br/>`--no-log-time`     | bool  | `False`   | Show date and time in logs                                                            |
| `cleanup`             | `--cleanup`<br/>`--no-cleanup`       | bool  | `True`    | Cleanup cache or temporary files after conversion                                     |
| `lower`               | `--lower`<br/>`--no-lower`           | bool  | `False`   | Lowercase words before writing                                                        |
| `utf8_check`          | `--utf8-check`<br/>`--no-utf8-check` | bool  | `True`    | Ensure entries contain valid UTF-8 strings                                            |
| `enable_alts`         | `--alts`<br/>`--no-alts`             | bool  | `True`    | Enable alternates                                                                     |
| `skip_resources`      | `--skip-resources`                   | bool  | `False`   | Skip resources (images, audio, etc)                                                   |
| `rtl`                 | `--rtl`                              | bool  | `False`   | Mark all definitions as Right-To-Left (definitions must be HTML)                      |
| `remove_html`         | `--remove-html`                      | str   |           | Remove given html tags (comma-separated) from definitions                             |
| `remove_html_all`     | `--remove-html-all`                  | bool  | `False`   | Remove all html tags from definitions                                                 |
| `normalize_html`      | `--normalize-html`                   | bool  | `False`   | Lowercase and normalize html tags in definitions                                      |
| `save_info_json`      | `--info`                             | bool  | `False`   | Save glossary info as json file with .info extension                                  |
| `color.cmd.critical`  |                                      | int   | `196`     | Color code for critical errors in terminal<br/>See [term_colors.md](./term_colors.md) |
| `color.cmd.error`     |                                      | int   | `1`       | Color code for errors in terminal<br/>See [term_colors.md](./term_colors.md)          |
| `color.cmd.warning`   |                                      | int   | `15`      | Color code for warnings in terminal<br/>See [term_colors.md](./term_colors.md)        |
| `ui_autoSetFormat`    |                                      | bool  | `True`    |                                                                                       |
| `reverse_matchWord`   |                                      | bool  | `True`    |                                                                                       |
| `reverse_showRel`     |                                      | str   | `Percent` |                                                                                       |
| `reverse_saveStep`    |                                      | int   | `1000`    |                                                                                       |
| `reverse_minRel`      |                                      | float | `0.3`     |                                                                                       |
| `reverse_maxNum`      |                                      | int   | `-1`      |                                                                                       |
| `reverse_includeDefs` |                                      | bool  | `False`   |                                                                                       |

## Configuration Files

The default configuration values are stored in [config.json](../config.json) file in source/installation directory.

The user configuration file - if exists - will override default configuration values.
The location of this file depends on the operating system:

- Linux or BSD: `~/.pyglossary/config.json`
- Mac: `~/Library/Preferences/PyGlossary/config.json`
- Windows: `C:\Users\USERNAME\AppData\Roaming\PyGlossary\config.json`

## Using as library

When you use PyGlossary as a library, neither of `config.json` files are loaded. So if you want to change the config, you should set `glos.config` property (which you can do only once for each instance of `Glossary`). For example:

```
glos = Glossary()
glos.config = {
	"lower": True,
}
```
