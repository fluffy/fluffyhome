FROM ubuntu:14.04
MAINTAINER Cullen Jennings <fluffy@iii.ca>

RUN apt-get update && apt-get dist-upgrade -y
RUN apt-get install -y git 
RUN apt-get install -y emacs24-nox

RUN apt-get install -y openjdk-7-jre-headless

RUN apt-get install -y wget  

RUN apt-get install -y ssh rsync
RUN apt-get install -y lsof

RUN apt-get install -y openssh-server openssh-client  

RUN cp /etc/ssh/sshd_config /etc/ssh/sshd_config.orig 
RUN cat /etc/ssh/sshd_config.orig | sed -e "s/Port 22/Port 5022/" > /etc/ssh/sshd_config
RUN ssh-keygen -t dsa -P '' -f ~/.ssh/id_dsa
RUN cat ~/.ssh/id_dsa.pub > ~/.ssh/authorized_keys
EXPOSE 5022

WORKDIR /tmp
RUN wget -nc https://archive.apache.org/dist/spark/spark-1.5.2/spark-1.5.2-bin-hadoop2.6.tgz
RUN tar xvfz spark-1.5.2-bin-hadoop2.6.tgz
RUN mv spark-1.5.2-bin-hadoop2.6 /usr/local/spark


#RUN mkdir /etc/hadoop
#RUN mkdir /var/lib/hadoop
#RUN mkdir /var/log/hadoop

ENV JAVA_HOME /usr/lib/jvm/java-1.7.0-openjdk-amd64

#ENV HADOOP_CONF_DIR /etc/hadoop
#ENV HADOOP_LOG_DIR /var/log/hadoop

ENV HADOOP_SSH_OPTS "-p 5022 -o ConnectTimeout=1 -o SendEnv=HADOOP_CONF_DIR"
RUN echo 'export JAVA_HOME=/usr/lib/jvm/java-1.7.0-openjdk-amd64' >> ~/.bashrc

#ENV HADOOP_PREFIX /usr/local/hadoop

#RUN cp /usr/local/hadoop/etc/hadoop/* /etc/hadoop/.
#COPY core-site.xml /etc/hadoop/core-site.xml
#COPY hdfs-site.xml /etc/hadoop/hdfs-site.xml
#COPY hadoop-env.sh /etc/hadoop/hadoop-env.sh


# HDFS URL port 
#EXPOSE 9000

# HDFS ports 50070=namenode-webui, 50075=datanode-webui, 50010=datanode-datatransfer 50020=databode-metadata 50090=secory-httpcheckpoint
#EXPOSE 50010 50020 50070 50075 50090

# no idea but on java for namenode
#EXPOSE 39412 


#RUN /usr/local/hadoop/bin/hdfs namenode -format

WORKDIR /root
COPY bootstrap.sh /root/bootstrap.sh

#VOLUME /var/log/hadoop

CMD /root/boostrap.sh -forever

ENV SPARK_MASTER_IP spark
ENV SPARK_WORKER_INSTANCES 1
ENV SPARK_WORKER_PORT 13894
ENV SPARK_WORKER_WEBUI_PORT 8081

# controller ports 6066=rest to submit apps, 7077=sparkMaster, 8080= masterUI
EXPOSE 6066 7077 8080

# worker ports 8081= working web gui, 13894 worker addres
EXPOSE 8081 13894
