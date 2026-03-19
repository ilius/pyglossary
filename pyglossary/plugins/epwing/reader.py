from __future__ import annotations
import os
import subprocess
import tempfile
import logging
from typing import TYPE_CHECKING

# Import the Yomichan reader from the existing plugin
try:
    from ..yomichan.reader import Reader as YomichanReader
except ImportError:
    # Fallback for different import contexts
    from pyglossary.plugins.yomichan.reader import Reader as YomichanReader

if TYPE_CHECKING:
    from pyglossary.glossary_types import EntryType, ReaderGlossaryType

log = logging.getLogger("pyglossary")

class Reader:
    def __init__(self, glos: ReaderGlossaryType) -> None:
        self._glos = glos
        self._yomichan_reader = YomichanReader(glos)
        self._temp_zip_path = ""
        self.filename = ""

    def open(self, filename: str) -> None:
        self.filename = filename
        if not os.path.isdir(filename):
            # If it's the CATALOGS file, use its parent directory
            if os.path.basename(filename).upper() == "CATALOGS":
                filename = os.path.dirname(filename)
            else:
                raise ValueError(f"EPWING: Input should be a directory, got {filename}")
        
        # Check for CATALOGS
        catalogs_path = os.path.join(filename, "CATALOGS")
        if not os.path.exists(catalogs_path):
            catalogs_path = os.path.join(filename, "catalogs")
            if not os.path.exists(catalogs_path):
                raise ValueError(f"EPWING: CATALOGS not found in {filename}")

        # Create a temporary file for the Yomichan ZIP
        temp_dir = tempfile.gettempdir()
        self._temp_zip_path = os.path.join(temp_dir, f"pyglossary_epwing_{os.path.basename(filename)}.zip")
        
        # Path to the yomichan binary (relative to this plugin)
        # Assuming yomichan.exe is in bin/ subdirectory of this plugin
        bin_dir = os.path.join(os.path.dirname(__file__), "bin")
        bin_path = os.path.join(bin_dir, "yomichan.exe")
        
        if not os.path.exists(bin_path):
             raise FileNotFoundError(f"EPWING: yomichan binary not found at {bin_path}")

        log.info(f"EPWING: Converting {filename} to temporary Yomichan format...")
        
        # Run the converter
        try:
            # We use the built binary from yomichan-import
            subprocess.run([
                bin_path,
                filename,
                self._temp_zip_path
            ], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            log.error(f"EPWING: Conversion failed: {e.stderr}")
            raise RuntimeError(f"EPWING conversion failed: {e.stderr}") from e
        
        log.info("EPWING: Conversion to Yomichan format successful.")
        
        # Now delegate reading to the Yomichan reader
        self._yomichan_reader.open(self._temp_zip_path)

    def close(self) -> None:
        self._yomichan_reader.close()
        if self._temp_zip_path and os.path.exists(self._temp_zip_path):
            try:
                os.remove(self._temp_zip_path)
            except OSError:
                pass
        self._temp_zip_path = ""

    def __len__(self) -> int:
        return len(self._yomichan_reader)

    def __iter__(self) -> Iterator[EntryType]:
        yield from self._yomichan_reader
