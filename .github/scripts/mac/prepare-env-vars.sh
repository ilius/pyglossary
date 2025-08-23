#!/usr/bin/env bash
# Use the environment variables set in the previous step
echo "C_INCLUDE_PATH=${PREFIX_LZO}/include:${PREFIX_LZO}/include/lzo" >> $GITHUB_ENV
echo "LIBRARY_PATH=${BREW_PREFIX}/lib" >> $GITHUB_ENV
echo "PKG_CONFIG_PATH=${BREW_PREFIX}/lib/pkgconfig:${PREFIX_ICU4C}/lib/pkgconfig:${PREFIX_LZO}/lib/pkgconfig:${PREFIX_LIBFFI}/lib/pkgconfig" >> $GITHUB_ENV
echo "LDFLAGS=-L${PREFIX_LIBFFI}/lib -L${PREFIX_ICU4C}/lib -L${PREFIX_LZO}/lib -L${BREW_PREFIX}/lib" >> $GITHUB_ENV
echo "CPPFLAGS=-I${PREFIX_ICU4C}/include -I${PREFIX_LIBFFI}/include -I${PREFIX_LZO}/include" >> $GITHUB_ENV
echo "DYLD_LIBRARY_PATH=${PREFIX_ICU4C}/lib:${PREFIX_LIBFFI}/lib:${PREFIX_LZO}/lib:${BREW_PREFIX}/lib" >> $GITHUB_ENV
echo "CC=clang" >> $GITHUB_ENV
echo "CXX=clang++" >> $GITHUB_ENV