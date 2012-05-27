

push:
	manage.py collectstatic --noinput
	git push heroku hero:master 

