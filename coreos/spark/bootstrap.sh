#!/bin/sh

service ssh start

ssh-keyscan -p 5022 10.1.3.10  >> ~/.ssh/known_hosts
ssh-keyscan -p 5022 localhost >> ~/.ssh/known_hosts
ssh-keyscan -p 5022 0.0.0.0 >> ~/.ssh/known_hosts
ssh-keyscan -p 5022 spark  >> ~/.ssh/known_hosts

#echo Y | /usr/local/hadoop/bin/hdfs namenode -format

#/usr/local/hadoop/sbin/start-dfs.sh

/usr/local/spark/sbin/start-master.sh
# ports 6066=rest to submit apps, 7077=sparkMaster, 8080= masterUI

/usr/local/spark/sbin/start-slave.sh spark://spark:7077
# ports 8081= working web gui, 

# apt-get install -y lsof
# lsof -n | grep LIST | sed -e "s/.*TCP/TCP/" | sort | uniq

if [ $# -eq 1 ]; then
    echo Done starting stuff 
    while true; do 
          sleep 1;
    done
fi
            
