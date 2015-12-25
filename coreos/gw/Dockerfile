FROM ubuntu:14.04
MAINTAINER Cullen Jennings <fluffy@iii.ca>

RUN apt-get update && apt-get dist-upgrade -y
RUN apt-get install -y git 
RUN apt-get install -y emacs24-nox

RUN apt-get install -y wget

RUN apt-get install -y golang

WORKDIR /tmp
COPY gw.go /tmp/gw.go


RUN mkdir /var/log/gw1


EXPOSE 11080

CMD /usr/local/bin/gw1 10.1.3.10:9092

