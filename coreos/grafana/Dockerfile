FROM ubuntu:14.04
MAINTAINER Cullen Jennings <fluffy@iii.ca>

RUN apt-get update && apt-get dist-upgrade -y
RUN apt-get install -y git 
RUN apt-get install -y emacs24-nox

RUN apt-get install -y libfontconfig
RUN apt-get install -y wget  
WORKDIR /tmp

RUN wget -nc https://grafanarel.s3.amazonaws.com/builds/grafana-2.6.0.linux-x64.tar.gz
RUN tar xvfz grafana-2.6.0.linux-x64.tar.gz
RUN mv grafana-2.6.0 /usr/local/grafana

RUN mkdir /var/lib/grafana
RUN mkdir /var/log/grafana

COPY grafana.cfg /etc/grafana.cfg

EXPOSE 3000
VOLUME /var/lib/grafana
VOLUME /var/log/grafana

CMD /usr/local/grafana/bin/grafana-server  -homepath /usr/local/grafana/ -config /etc/grafana.cfg

