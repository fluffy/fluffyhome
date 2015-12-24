# build docker container

docker build -t fluffy/zookeeper .

# run shell

docker run -i -t  -p 2181:2181  -v /data/zookeeper:/var/lib/zookeeper  fluffy/zookeeper /bin/bash

# run

docker run -d -p 2181:2181 --name zookeeper -v /data/zookeeper:/var/lib/zookeeper fluffy/zookeeper

