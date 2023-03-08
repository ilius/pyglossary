'\nwcwidth module.\n\nhttps://github.com/jquast/wcwidth\n'
from .wcwidth import (
    WIDE_EASTASIAN,
    ZERO_WIDTH,
    _bisearch,
    _wcmatch_version,
    _wcversion_value,
    list_versions,
    wcswidth,
    wcwidth,
)

__all__='wcwidth','wcswidth','list_versions'
__version__='0.2.6'