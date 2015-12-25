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
RUN go build gw1.go
RUN cp /tmp/gw1 /usr/local/bin/gw1


EXPOSE 11080

CMD /usr/local/bin/gw1 -port 11080 -out 10.1.3.10:9092

