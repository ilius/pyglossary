FROM bitnami/minideb
MAINTAINER Saeed Rasooli saeed.gnu@gmail.com
LABEL Description="Dockefile to run PyGlossary inside a Debian-based Docker image"

COPY . /opt/pyglossary

RUN /opt/pyglossary/scripts/docker-deb-setup.sh

CMD python3 /opt/pyglossary/main.py --cmd
