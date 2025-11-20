#!/bin/sh

xargs -n1 shellcheck --exclude=SC2046,SC2148 <.sh-list
