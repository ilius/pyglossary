## Gtk3 interface requirements

- Debian/Ubuntu: `apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`
- openSUSE: `zypper install python3-gobject gtk3`
- Fedora: `dnf install pygobject3 python3-gobject gtk3`
- ArchLinux:
- `pacman -S python-gobject gtk3`
- https://aur.archlinux.org/packages/pyglossary/
- Mac OS X: `brew install pygobject3 gtk+3`
- Nix / NixOS: `nix-shell -p pkgs.gobject-introspection python38Packages.pygobject3 python38Packages.pycairo`
