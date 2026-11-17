## Gtk3 interface requirements

- Debian/Ubuntu: `apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`
- openSUSE: `zypper install python3-gobject gtk3`
- Fedora: `dnf install pygobject3 python3-gobject gtk3`
- ArchLinux: `pacman -S python-gobject gtk3`
- Mac OS X: `brew install pygobject3 gtk+3`

## Flatpak

The Flatpak dialogs use the desktop portal, which grants access to the selected
file or folder only. For output, the Gtk3 UI therefore selects an output
folder instead of a single file and derives the output filename from the input
file and the selected output format. This allows formats that write multiple
files or a resource directory, such as StarDict, to work inside the sandbox.

To test the Flatpak behavior outside a sandbox, set `PYGLOSSARY_FLATPAK=1`.
