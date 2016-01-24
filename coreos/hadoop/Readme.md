# build docker container

docker build -t fluffy/hadoop .

# run shell

docker run -i -t   -p 4022:4022  -p 9000:9000  -p 50010:50010 -p 50020:50020 -p 50070:50070 -p 50075:50075 -p 50090:50090 -p  39412:39412   --name hadoop fluffy/hadoop /bin/bash

# test hadoop

echo hi > /tmp/foo ; bin/hadoop fs -put /tmp/foo hdfs://hadoop:9000/junk3.txt

bin/hadoop fs -ls hdfs://hadoop:9000/

bin/hadoop fs -mkdir  hdfs://hadoop:9000/junk 
bin/hadoop fs -chmod a+rwx  hdfs://hadoop:9000/junk 

echo hello > /tmp/foo ; bin/hadoop fs -put /tmp/foo hdfs://hadoop:9000/junk/junk4.txt


# run

docker run -d -p 4022:4022 -p 9000:9000  -p 50010:50010 -p 50020:50020 -p 50070:50070 -p 50075:50075 -p 50090:50090 -p  39412:39412 --name hadoop fluffy/hadoop

