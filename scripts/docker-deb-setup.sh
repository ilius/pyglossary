#!/bin/bash

rm /etc/apt/apt.conf.d/docker-clean

set -e

apt-get update

apt-get install --yes python3
apt-get install --yes python3-pip
apt-get install --yes python3-lxml
apt-get install --yes python3-lzo
apt-get install --yes python3-icu
apt-get install --yes pkg-config
apt-get install --yes python3-prompt-toolkit
apt-get install --yes python3-bs4
apt-get install --yes python3-marisa
apt-get install --yes python3-libzim
apt-get install --yes python3-mistune

rm /usr/lib/python*/EXTERNALLY-MANAGED
