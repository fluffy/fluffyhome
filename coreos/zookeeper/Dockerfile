FROM ubuntu:trusty
RUN apt-get update && apt-get dist-upgrade -y
RUN apt-get install -y zookeeper

CMD [“/usr/share/zookeeper/bin/zkServer.sh”, “start-foreground”]
