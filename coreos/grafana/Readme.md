# build docker container

docker build -t fluffy/grafana .

# run shell

docker run -i -t  -p 3000:3000 fluffy/grafana /bin/bash

# test graphana

Go to  http://10.1.3.10:3000/
Log on with user admin pwd admin

# run

docker run -d -p 3000:3000 --name grafana -v /data/graphana:/var/lib/grafana fluffy/grafana

