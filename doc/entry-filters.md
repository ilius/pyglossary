## Entry Filters

| Name                         | Default Enabled | Command Flags                        | Description                                 |
| ---------------------------- | --------------- | ------------------------------------ | ------------------------------------------- |
| `strip`                      | Yes             |                                      | Strip whitespaces in word(s) and definition |
| `non_empty_word`             | Yes             |                                      | Skip entries with empty word                |
| `skip_resources`             | No              | `--skip-resources`                   | Skip resources / data files                 |
| `utf8_check`                 | No              | `--utf8-check`<br/>`--no-utf8-check` | Fix Unicode in word(s) and definition       |
| `lower`                      | No              | `--lower`<br/>`--no-lower`           | Lowercase word(s)                           |
| `rtl`                        | No              | `--rtl`                              | Make definition right-to-left               |
| `remove_html_all`            | No              | `--remove-html-all`                  | Remove all HTML tags from definition        |
| `remove_html`                | No              | `--remove-html`                      | Remove specific HTML tags from definition   |
| `normalize_html`             | No              | `--normalize-html`                   | Normalize HTML tags in definition (WIP)     |
| `lang`                       | Yes             |                                      | Language-specific cleanup/fixes             |
| `non_empty_word`             | Yes             |                                      | Skip entries with empty word                |
| `non_empty_defi`             | Yes             |                                      | Skip entries with empty definition          |
| `remove_empty_dup_alt_words` | Yes             |                                      | Remove empty and duplicate alternate words  |
