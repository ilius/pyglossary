from copy import copy
import os
import shutil
import sys
import time
from typing import Tuple, Union
from zipfile import ZIP_LZMA, ZipFile, ZipInfo

try:
    from zipfile import _MASK_COMPRESS_OPTION_1  # type: ignore[attr-defined]
except ImportError:
    _MASK_COMPRESS_OPTION_1 = 0x02

__version__ = "0.3.1"


def date_time() -> Union[time.struct_time, Tuple[int, int, int, int, int, int]]:
    """Returns date_time value used to force overwrite on all ZipInfo objects. Defaults to
    1980-01-01 00:00:00. You can set this with the environment variable SOURCE_DATE_EPOCH as an
    integer value representing seconds since Epoch.
    """
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH", None)
    if source_date_epoch is not None:
        return time.gmtime(int(source_date_epoch))
    return (1980, 1, 1, 0, 0, 0)


def file_mode() -> int:
    """Returns the file permissions mode value used to force overwrite on all ZipInfo objects.
    Defaults to 0o644 (rw-r--r--). You can set this with the environment variable
    REPRO_ZIPFILE_FILE_MODE. It should be in the Unix standard three-digit octal representation
    (e.g., '644').
    """
    file_mode_env = os.environ.get("REPRO_ZIPFILE_FILE_MODE", None)
    if file_mode_env is not None:
        return int(file_mode_env, 8)
    return 0o644


def dir_mode() -> int:
    """Returns the directory permissions mode value used to force overwrite on all ZipInfo objects.
    Defaults to 0o755 (rwxr-xr-x). You can set this with the environment variable
    REPRO_ZIPFILE_DIR_MODE. It should be in the Unix standard three-digit octal representation
    (e.g., '755').
    """
    dir_mode_env = os.environ.get("REPRO_ZIPFILE_DIR_MODE", None)
    if dir_mode_env is not None:
        return int(dir_mode_env, 8)
    return 0o755


class ReproducibleZipFile(ZipFile):
    """Open a ZIP file, where file can be a path to a file (a string), a file-like object or a
    path-like object.

    This is a replacement for the Python standard library zipfile.ZipFile that overwrites
    file-modified timestamps and file/directory permissions modes in write mode in order to create
    a reproducible ZIP archive. Other than overwriting these values, it works the same way as
    zipfile.ZipFile. For documentation on use, see the Python documentation for zipfile:
    https://docs.python.org/3/library/zipfile.html
    """

    # Following method modified from Python 3.11
    # https://github.com/python/cpython/blob/202efe1a3bcd499f3bf17bd953c6d36d47747e78/Lib/zipfile.py#L1763-L1794
    # Copyright Python Software Foundation, licensed under PSF License Version 2
    # See LICENSE file for full license agreement and notice of copyright
    def write(self, filename, arcname=None, compress_type=None, compresslevel=None):
        """Put the bytes from filename into the archive under the name arcname."""

        if not self.fp:
            raise ValueError("Attempt to write to ZIP archive that was already closed")
        if self._writing:
            raise ValueError("Can't write to ZIP archive while an open writing handle exists")

        zinfo = ZipInfo.from_file(filename, arcname, strict_timestamps=self._strict_timestamps)

        ## repro-zipfile ADDED ##
        # Overwrite date_time and extrnal_attr (permissions mode)
        zinfo = copy(zinfo)
        zinfo.date_time = date_time()
        if zinfo.is_dir():
            zinfo.external_attr = (0o40000 | dir_mode()) << 16
            zinfo.external_attr |= 0x10  # MS-DOS directory flag
        else:
            zinfo.external_attr = file_mode() << 16
        #########################

        if zinfo.is_dir():
            zinfo.compress_size = 0
            zinfo.CRC = 0
            self.mkdir(zinfo)
        else:
            if compress_type is not None:
                zinfo.compress_type = compress_type
            else:
                zinfo.compress_type = self.compression

            if compresslevel is not None:
                zinfo._compresslevel = compresslevel
            else:
                zinfo._compresslevel = self.compresslevel

            with open(filename, "rb") as src, self.open(zinfo, "w") as dest:
                shutil.copyfileobj(src, dest, 1024 * 8)

    # Following method modified from Python 3.11
    # https://github.com/python/cpython/blob/202efe1a3bcd499f3bf17bd953c6d36d47747e78/Lib/zipfile.py#L1796-L1835
    # Copyright Python Software Foundation, licensed under PSF License Version 2
    # See LICENSE file for full license agreement and notice of copyright
    def writestr(self, zinfo_or_arcname, data, compress_type=None, compresslevel=None):
        """Write a file into the archive.  The contents is 'data', which may be either a 'str' or
        a 'bytes' instance; if it is a 'str', it is encoded as UTF-8 first. 'zinfo_or_arcname' is
        either a ZipInfo instance or the name of the file in the archive."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        if not isinstance(zinfo_or_arcname, ZipInfo):
            zinfo = ZipInfo(filename=zinfo_or_arcname, date_time=time.localtime(time.time())[:6])
            zinfo.compress_type = self.compression
            zinfo._compresslevel = self.compresslevel
            if zinfo.filename.endswith("/"):
                zinfo.external_attr = 0o40775 << 16  # drwxrwxr-x
                zinfo.external_attr |= 0x10  # MS-DOS directory flag
            else:
                zinfo.external_attr = 0o600 << 16  # ?rw-------
        else:
            zinfo = zinfo_or_arcname

        ## repro-zipfile ADDED ##
        # Overwrite date_time and extrnal_attr (permissions mode)
        zinfo = copy(zinfo)
        zinfo.date_time = date_time()
        if zinfo.is_dir():
            zinfo.external_attr = (0o40000 | dir_mode()) << 16
            zinfo.external_attr |= 0x10  # MS-DOS directory flag
        else:
            zinfo.external_attr = file_mode() << 16
        #########################

        if not self.fp:
            raise ValueError("Attempt to write to ZIP archive that was already closed")
        if self._writing:
            raise ValueError("Can't write to ZIP archive while an open writing handle exists.")

        if compress_type is not None:
            zinfo.compress_type = compress_type

        if compresslevel is not None:
            zinfo._compresslevel = compresslevel

        zinfo.file_size = len(data)  # Uncompressed size
        with self._lock:
            with self.open(zinfo, mode="w") as dest:
                dest.write(data)

    if sys.version_info < (3, 11):
        # Following method modified from Python 3.11
        # https://github.com/python/cpython/blob/202efe1a3bcd499f3bf17bd953c6d36d47747e78/Lib/zipfile.py#L1837-L1870
        # Copyright Python Software Foundation, licensed under PSF License Version 2
        # See LICENSE file for full license agreement and notice of copyright
        def mkdir(self, zinfo_or_directory_name, mode=511):
            """Creates a directory inside the zip archive."""
            if isinstance(zinfo_or_directory_name, ZipInfo):
                zinfo = zinfo_or_directory_name
                if not zinfo.is_dir():
                    raise ValueError("The given ZipInfo does not describe a directory")
            elif isinstance(zinfo_or_directory_name, str):
                directory_name = zinfo_or_directory_name
                if not directory_name.endswith("/"):
                    directory_name += "/"
                zinfo = ZipInfo(directory_name)
                zinfo.compress_size = 0
                zinfo.CRC = 0
                zinfo.external_attr = ((0o40000 | mode) & 0xFFFF) << 16
                zinfo.file_size = 0
                zinfo.external_attr |= 0x10
            else:
                raise TypeError("Expected type str or ZipInfo")

            ## repro-zipfile ADDED ##
            # Overwrite date_time and extrnal_attr (permissions mode)
            zinfo = copy(zinfo)
            zinfo.date_time = date_time()
            zinfo.external_attr = (0o40000 | dir_mode()) << 16
            zinfo.external_attr |= 0x10  # MS-DOS directory flag
            #########################

            with self._lock:
                if self._seekable:
                    self.fp.seek(self.start_dir)
                zinfo.header_offset = self.fp.tell()  # Start of header bytes
                if zinfo.compress_type == ZIP_LZMA:
                    # Compressed data includes an end-of-stream (EOS) marker
                    zinfo.flag_bits |= _MASK_COMPRESS_OPTION_1

                self._writecheck(zinfo)
                self._didModify = True

                self.filelist.append(zinfo)
                self.NameToInfo[zinfo.filename] = zinfo
                self.fp.write(zinfo.FileHeader(False))
                self.start_dir = self.fp.tell()
