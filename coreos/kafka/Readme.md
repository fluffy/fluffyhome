# build docker container

docker build -t fluffy/kafka .

# run shell

docker run -i -t  -p 2181:2181  -v /data/kafka:/var/lib/kafka  fluffy/kafka /bin/bash

# run

docker run -d -p 2181:2181 --name kafka -v /data/kafka:/var/lib/kafka fluffy/kafka

