FROM bitnami/minideb
MAINTAINER Saeed Rasooli saeed.gnu@gmail.com
LABEL Description="Dockefile to run PyGlossary inside a Debian-based Docker image"

COPY . /opt/pyglossary

RUN apt-get update
RUN apt-get install --yes python3
RUN apt-get install --yes python3-pip
RUN apt-get install --yes python3-lxml
RUN apt-get install --yes python3-lzo
RUN apt-get install --yes python3-icu
RUN apt-get install --yes pkg-config
RUN pip3 install prompt_toolkit
RUN pip3 install beautifulsoup4
RUN pip3 install marisa-trie
RUN pip3 install libzim

WORKDIR /root
CMD python3 /opt/pyglossary/main.py --cmd
