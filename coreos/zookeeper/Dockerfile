FROM ubuntu:14.04
MAINTAINER Cullen Jennings <fluffy@iii.ca>

RUN apt-get update && apt-get dist-upgrade -y
RUN apt-get install -y git 
RUN apt-get install -y emacs24-nox

RUN apt-get install -y openjdk-7-jre-headless

RUN apt-get install -y zookeeper

COPY zoo.cfg /etc/zookeeper/conf/zoo.cfg

MKDIR /data

EXPOSE 2181
VOLUME /var/lib/zookeeper


CMD [“/usr/share/zookeeper/bin/zkServer.sh”, “start-foreground”]
