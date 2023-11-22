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

rm /usr/lib/python*/EXTERNALLY-MANAGED

pip3 install prompt_toolkit
pip3 install beautifulsoup4
pip3 install marisa-trie
pip3 install 'libzim>=1.0'
pip3 install 'mistune==3.0.1'

