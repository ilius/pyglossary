FROM bitnami/minideb
MAINTAINER Saeed Rasooli saeed.gnu@gmail.com
LABEL Description="Dockefile to run PyGlossary inside a Debian-based Docker image"

COPY . /opt/pyglossary

RUN /opt/pyglossary/scripts/docker-deb-setup.sh
RUN mkdir -p /root/home

WORKDIR /root/home
CMD python3 /opt/pyglossary/main.py --cmd
