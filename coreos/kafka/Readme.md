# build docker container

docker build -t fluffy/kafka .

# run shell

docker run -i -t   fluffy/kafka /bin/bash

# test kafka

## create topic
docker run -i -t  fluffy/kafka /usr/local/kafka/bin/kafka-topics.sh --zookeeper 10.1.3.10:2181 --create --replication-factor 1 --partitions 1 -topic test

## list topics 
docker run -i -t  fluffy/kafka /usr/local/kafka/bin/kafka-topics.sh --zookeeper 10.1.3.10:2181 --list

## print data
docker run -i -t  fluffy/kafka /usr/local/kafka/bin/kafka-console-consumer.sh --zookeeper 10.1.3.10:2181 -from-beginning -topic test 

# run

docker run -d -p 9092:9092 --name kafka -v /data/kafka:/var/lib/kafka fluffy/kafka

