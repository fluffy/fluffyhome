Energy Graph
==================

Django application to graph results of home energy monitor 

---------
# How to set up new machine 

Build a linux node with firewall, ssh, and fluffy user - see linode-script.sh

Build and boot setting up password for user fluffy

set up DNS to point to new server 

ssh on to it and set up ssh key for remote login if not done by linnode script 

generate ssh key with 
ssh-keygen -help -t rsa -C "fluffy@iii.ca"
cat ~/.ssh/id_rsa.pub 
put that key in github repo 
do a 
ssh git@github.com
and verify fingerprint 

set up reverse DNS 


do a 
fab deployServer

edit the licence key in newrelic.ini

On the new host do 
cd src/fluffyhome/energygraph; 
../manage.py createsuperuser --username=fluffy --email=fluffy@iii.ca
and set up password for django supersuer 

go to 
http://fh4.fluffyhome.com/admin-django/
and set add user wind 
then go to 
http://fh4.fluffyhome.com/admin-django/store/user/
and depending on auth model may need to update passowrd 

------------------------------------------------------------------
# Random noes on DataBase usage 

sudo -u postgres psql
DROP USER fluffy ; 
CREATE USER fluffy WITH PASSWORD 'myPassword';
GRANT ALL PRIVILEGES ON DATABASE energygraph to fluffy;
\q

Might try 
sudo -u postgres createdb --owner fluffy energygraph 

Can also set password in psql with 
\password fluffy



You can muck with DB with 
psql -d energygraph -U fluffy -h localhost
SELECT "userID", "userName", "passwd" FROM store_user ORDER BY "userID" ;
SELECT "sensorID", "userID", "sensorName" FROM store_sensor ORDER BY "sensorID";
can fix up passwords with
UPDATE store_user SET "passwd" = 'newpwd'  WHERE "userID" = 5 ;
right now am using django auth passwords on one in this DB so that does not
matter 

ECM1240-5723-aux5 for user 3 (plagd)   is sensorID 115 
ECM1240-42340-ch2 for user 1 cullen is sensorid 40 aka "Dryer ECM1c2"

mongo 
use energygraph
show collections
db.measurements1.find( { sensorID: 40 } , { time: true, value: true  }  ).sort({ time: -11 } ).limit(5)
db.measurements1.find( { sensorID: 115 } , { time: true, value: true,integral:true   }  ).sort( { time: -1 } ).limit(10)

b.hourly1.find( { sensorID: 40 }, { time: true, value:
true,integral:true,hourOfWeek:true   }  ).sort( { time: -1 } ).limit( 20 )


can monitors task in celery with a web server started with 
celery flower --broker=redis://localhost:6379/0


---------------------------
# environment setup for local devel 

Set up following environment variables

setenv DATABASE_URL postgres://fluffy:pwd@localhost/hero
setenv DJANGO_SECRET_KEY junkhere

setenv REDISTOGO_URL redis://localhost:6379

setenv DJANGO_DEBUG TRUE

setenv AWS_ACCESS_KEY_ID "foobar"
setenv AWS_SECRET_ACCESS_KEY "barfoo"



On my local devel mac, for the celry cron jobs use 
../manage.py celery worker --loglevel=info -E -B

and run main program with 
../manage.py runserver

deploy with
fab deploy
