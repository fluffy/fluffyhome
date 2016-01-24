# build docker container

docker build -t fluffy/spark .

# run shell

docker run -i -t   -p 6066:6066 -p 7077:7077 -p 8080:8080  -p 8081:8081   -p 13894:13894      -p 5022:5022  -p 9000:9000  -p 50010:50010 -p 50020:50020 -p 50070:50070 -p 50075:50075 -p 50090:50090 -p  39412:39412   --name spark fluffy/spark /bin/bash

# test spark

echo hi > /tmp/foo ; bin/spark fs -put /tmp/foo hdfs://spark:9000/junk3.txt

bin/spark fs -ls hdfs://spark:9000/

bin/spark fs -mkdir  hdfs://spark:9000/junk 
bin/spark fs -chmod a+rwx  hdfs://spark:9000/junk 

echo hello > /tmp/foo ; bin/spark fs -put /tmp/foo hdfs://spark:9000/junk/junk4.txt


# run

docker run -d -p 5022:5022 -p 9000:9000  -p 50010:50010 -p 50020:50020 -p 50070:50070 -p 50075:50075 -p 50090:50090 -p  39412:39412 --name spark fluffy/spark

