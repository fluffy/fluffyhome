FROM ubuntu:14.04
MAINTAINER Cullen Jennings <fluffy@iii.ca>

RUN apt-get update && apt-get dist-upgrade -y
RUN apt-get install -y git 
RUN apt-get install -y emacs24-nox

#RUN apt-get install -y openjdk-7-jre-headless

#RUN apt-get install -y wget  
#WORKDIR /tmp
#RUN wget -nc  https://archive.apache.org/dist/kafka/0.9.0.0/kafka_2.11-0.9.0.0.tgz
#RUN tar xvfz kafka_2.11-0.9.0.0.tgz
#RUN mv kafka_2.11-0.9.0.0/ /usr/local/kafka

#RUN mkdir /var/lib/kafka
#RUN mkdir /var/log/kafka

#COPY kafka.cfg /etc/kafka.cfg

#EXPOSE 9092
#VOLUME /var/lib/kafka

#CMD /usr/local/kafka/bin/kafka-server-start.sh /etc/kafka.cfg

