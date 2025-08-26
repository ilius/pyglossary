#!/usr/bin/env bash

source .venv/bin/activate

# Export vars
export PKG_CONFIG_PATH="${BREW_PREFIX}/lib/pkgconfig:${PREFIX_ICU4C}/lib/pkgconfig:${PREFIX_LZO}/lib/pkgconfig:${PREFIX_LIBFFI}/lib/pkgconfig"
export LDFLAGS="-L${PREFIX_LIBFFI}/lib -L${PREFIX_ICU4C}/lib -L${PREFIX_LZO}/lib -L${BREW_PREFIX}/lib"
export CPPFLAGS="-I${PREFIX_ICU4C}/include -I${PREFIX_LIBFFI}/include -I${PREFIX_LZO}/include"
export DYLD_LIBRARY_PATH="${PREFIX_ICU4C}/lib:${PREFIX_LIBFFI}/lib:${PREFIX_LZO}/lib:${BREW_PREFIX}/lib"
export CC=clang
export CXX=clang++

# NUITKA
uv pip install -U nuitka

# DEPENDENCIES THAT NEED COMPILATION

########### Install PyICU with static deps ##############
STATIC_DEPS=true uv pip install --no-binary PyICU PyICU

########### Install python-lzo with static deps ##############
### ALSO SEE: https://github.com/Nuitka/Nuitka/issues/2580#issuecomment-1895611093
STATIC_DEPS=true uv pip install --no-binary python-lzo python-lzo

uv pip install -r requirements.txt
