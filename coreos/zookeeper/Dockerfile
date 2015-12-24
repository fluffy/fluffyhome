FROM ubuntu:14.04
MAINTAINER Cullen Jennings <fluffy@iii.ca>

RUN apt-get update && apt-get dist-upgrade -y
RUN apt-get install -y git 
RUN apt-get install -y emacs24-nox

RUN apt-get install -y zookeeper

ADD zookeeper.properties /etc/TODODDODODOD

EXPOSE 2181 

CMD [“/usr/share/zookeeper/bin/zkServer.sh”, “start-foreground”]
