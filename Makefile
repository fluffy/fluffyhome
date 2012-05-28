

deploy:
	manage.py collectstatic --noinput
	heroku maintenance:on
	git push heroku hero:master 
	heroku maintenance:off


run:
	foreman start


log:
	heroku logs -t 

