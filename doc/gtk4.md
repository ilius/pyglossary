## Gtk4 interface requirements

- Debian/Ubuntu: `apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0`
- openSUSE: `zypper install python3-gobject gtk4`
- Fedora: `dnf install pygobject3 python3-gobject gtk4`
- ArchLinux: `pacman -S python-gobject gtk4`
- Mac OS X: `brew install pygobject3 gtk4`

## Flatpak

The Flatpak dialogs use the desktop portal, which grants access to the selected
file or folder only. For output, the Gtk4 UI therefore selects an output
folder instead of a single file and derives the output filename from the input
file and the selected output format. This allows formats that write multiple
files or a resource directory, such as StarDict, to work inside the sandbox.

To test the Flatpak behavior outside a sandbox, set `PYGLOSSARY_FLATPAK=1`.
