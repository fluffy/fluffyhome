# build docker container

docker build -t fluffy/kafka .

# run shell

docker run -i -t  -p 9092:9092  -v /data/kafka:/var/lib/kafka  fluffy/kafka /bin/bash

# run

docker run -d -p 9092:9092 --name kafka -v /data/kafka:/var/lib/kafka fluffy/kafka

