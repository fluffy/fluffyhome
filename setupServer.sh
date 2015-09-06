
#echo install ssh authorized keys to login 

#sudo echo "fluffy ALL = NOPASSWD: ALL"  > /etc/sudoers.d/cullen ; 
#sudo chmod 0440 /etc/sudoers.d/cullen 
#sudo echo "fluffy ALL=(postgres) NOPASSWD: ALL"  >> /etc/sudoers.d/cullen

sudo apt-get update
   
sudo apt-get -y install ufw
sudo ufw default deny
sudo ufw logging on
sudo ufw allow ssh/tcp
sudo ufw limit ssh/tcp
sudo ufw allow http/tcp
sudo ufw allow https/tcp
#sudo ufw allow http-alt/tcp
echo y | sudo ufw enable

sudo apt-get -y upgrade
#echo you might want to reboot your server about here 


sudo apt-get -y install fail2ban
sudo apt-get -y install logcheck logcheck-database

echo "America/Edmonton" | sudo tee /etc/timezone
sudo dpkg-reconfigure --frontend noninteractive tzdata

#sudo apt-get -y remove ax25-node libax25

sudo apt-get -y install emacs23-nox git-core build-essential gcc tcsh

ssh-keyscan -H github.com >> ~/.ssh/known_hosts

sudo apt-get -y install curl 

#sudo sh -c 'echo "deb http://stable.packages.cloudmonitoring.rackspace.com/ubuntu-14.04-x86_64 cloudmonitoring main" > /etc/apt/sources.list.d/rackspace-monitoring-agent.list'
#curl https://monitoring.api.rackspacecloud.com/pki/agent/linux.asc | sudo apt-key add -
#sudo apt-get update
#sudo apt-get install rackspace-monitoring-agent

#sudo apt-get -y install mongodb
#sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
#sudo sh -c 'echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" > /etc/apt/sources.list.d/mongodb.list '
#sudo apt-get update
#sudo apt-get -y install mongodb-org

sudo apt-get -y install mongodb 
sudo apt-get -y install python-pymongo

#sudo apt-get -y install redis
sudo apt-get -y install redis-server
#sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.default
#sudo service redis-server restart

#curl http://www.rabbitmq.com/rabbitmq-signing-key-public.asc  | sudo apt-key add -
#sudo sh -c 'echo "deb http://www.rabbitmq.com/debian/ testing main" > /etc/apt/sources.list.d/rabbitmq.list '
#sudo apt-get update
sudo apt-get -y install rabbitmq-server 

#sudo apt-get -y install nodejs
#sudo apt-get -y install npm 

# Forever seems to need this 
#sudo ln -s `which nodejs` /usr/local/bin/node
#sudo apt-get -y install node-legacy
#sudo npm install -g forever
#sudo npm install -g forever-monitor
    
#sudo npm install -g bower

# no idea why trying this twice is better
#sudo npm install -g forever
#sudo npm install -g forever-monitor

sudo apt-get -y install nginx 

sudo rm /etc/nginx/sites-enabled/default

sudo apt-get -y install python-django

sudo apt-get -y install postgresql postgresql-contrib

sudo apt-get -y install uwsgi 
sudo apt-get -y install uwsgi-plugin-python3
sudo apt-get -y install uwsgi-plugin-python

sudo  apt-get -y  install python-pip

pip install uwsgitop


echo do the stuff in energeygraph/fab.py file for deploy server


sudo cp /home/fluffy/src/fluffyhome/fluffyhome-uwsgi.ini /etc/uwsgi/apps-available/fluffyhome-uwsgi.ini
sudo ln -s /etc/uwsgi/apps-available/fluffyhome-uwsgi.ini /etc/uwsgi/apps-enabled/fluffyhome-uwsgi.ini

sudo cp /home/fluffy/src/fluffyhome/fluffyhome-nginx.conf  /etc/nginx/sites-available/fluffyhome-nginx.conf
sudo ln -s /etc/nginx/sites-available/fluffyhome-nginx.conf /etc/nginx/sites-enabled/fluffyhome-nginx.conf



