# build docker container

docker build -t fluffy/graphana .

# run shell

docker run -i -t   fluffy/graphana /bin/bash

# test graphana


# run

docker run -d -p 3000:3000 --name graphana -v /data/graphana:/var/lib/graphana fluffy/graphana

