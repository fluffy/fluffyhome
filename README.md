fluffyhome
==========

Home Energy Monitoring Tools 




-----------
# Heroku Notes 

Deploy the hero branch to the master branch of heroku remote 

git push heroku hero:master 

heroku run python manage.py syncdb



# Testing notes 

Look at the wiki for some notes on creating users and adding values




# reset DB on herok 

heroku run python manage.py syncdb
heroku run python manage.py syncdb

Need to go to /admin to create accounts for auth and seperate creade data accounts


#reset redis 
heroku run python
import os
import redis
url = os.getenv('REDISTOGO_URL', 'redis://localhost')
r = redis.from_url(redis_url) 
r.flushdb()





