# build docker container

docker build -t fluffy/gw1 .

# run shell

docker run -i -t  -p 9092:9092   fluffy/gw1 /bin/bash

# run

docker run -d -p 11080:11080 --name gw1  fluffy/gw1

