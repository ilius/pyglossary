# Sort Key

## Supported `sortKey` names / `--sort-key` argument values

| Name/Value             | Description               | Default for formats                               | Supports `--sort-locale` |
| ---------------------- | ------------------------- | ------------------------------------------------- | :----------------------: |
| `headword`             | Headword                  |                                                   | Yes                      |
| `headword_lower`       | Lowercase Headword        | All other formats (given `--sort`)                | Yes                      |
| `headword_bytes_lower` | ASCII-Lowercase Headword  |                                                   | No                       |
| `stardict`             | StarDict                  | [StarDict](./p/stardict.md)                       | No                       |
| `ebook`                | E-Book (prefix length: 2) | [EPUB-2](./p/epub2.md), [Mobipocket](./p/mobi.md) | No                       |
| `ebook_length3`        | E-Book (prefix length: 3) |                                                   | No                       |
| `dicformids`           | DictionaryForMIDs         | [DictionaryForMIDs](./p/dicformids.md)            | No                       |
| `random`               | Random                    |                                                   | Yes                      |

## Sort Locale

You can pass an [ICU Locale name/identifier](https://unicode-org.github.io/icu/userguide/locale/) as part of `sortKey` / `--sort-key` value, after a `:` symbol. For example:

- `--sort-key=:fa_IR.UTF-8`: Persian (then case-insensitive Latin)
- `--sort-key=headword:fa_IR.UTF-8`: Persian (then case-sensitive Latin)
- `--sort-key=headword:es`: case-sensitive Spanish
- `--sort-key=headword_lower:es`: case-insensitive Spanish
- `--sort-key=:es`: Spanish (case-insensitive by default)
- `--sort-key=:latn-arab`: first Latin, then Arabic
- `--sort-key=:fa-u-kr-latn-arab`: first Latin, then Persian
