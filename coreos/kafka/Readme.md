# build docker container

docker build -t fluffy/kafka .

# run shell

docker run -i -t   fluffy/kafka /bin/bash

# create topic

docker run -i -t  fluffy/kafka /usr/local/kafka/bin/kafka-topics.sh --create --zookeeper 10.1.3.10:2181 --replication-factor 1 --partitions 1 -topic test


# run

docker run -d -p 9092:9092 --name kafka -v /data/kafka:/var/lib/kafka fluffy/kafka

