#!/bin/sh

service ssh start

ssh-keyscan -p 4022 10.1.3.10  >> ~/.ssh/known_hosts
ssh-keyscan -p 4022 localhost >> ~/.ssh/known_hosts
ssh-keyscan -p 4022 0.0.0.0 >> ~/.ssh/known_hosts
ssh-keyscan -p 4022 hadoop  >> ~/.ssh/known_hosts

/usr/local/hadoop/sbin/start-dfs.sh

# apt-get install -y lsof
# lsof | grep LIST | sed -e "s/.*TCP/TCP/" | sort | uniq

if [ $# -eq 1 ]; then
    echo Done starting stuff 
    while true; do 
          sleep 1;
    done
fi
            
