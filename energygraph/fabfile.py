
from fabric.api import *

@task
@hosts('fh3.fluffyhome.com')
def deploy():
    """ Get the code on report host """
    run( "cd src/fluffyhome; git pull" );
    run( "cd src/fluffyhome/energygraph; sudo pip install -q -r requirements.txt ");
    run( "cd src/fluffyhome/; ./manage.py syncdb ");
    run( "cd src/fluffyhome/; ./manage.py migrate store ");
    run( "cd src/fluffyhome/; ./manage.py collectstatic -v 1 --noinput");
    run( "sudo supervisorctl reload" )
    run( "sudo supervisorctl restart celery" )
    run( "sudo apache2ctl restart" )


@task
def build():
    """ Make all the local stuff and push to github for deployment """
    local( "../manage.py syncdb" );
    local( "pip freeze > requirements.txt ");
    local( "git commit --allow-empty -a -m 'update from build' " );
    local( "git push" );


@task
def cron():
    """ Run local celery working to run cron jobs """
    local( "../manage.py celery worker --loglevel=info -E -B" );


@task
def web():
    """ Run local webserver """
    local( "../manage.py runserver" );


@task
def loaddata():
    """ Load some test data in local server """
    local( "./uploadDump.py ~/Documents/FluffyHomeData/all-dump.xml" )
    local( "./uploadDump.py ~/Documents/FluffyHomeData/fluffy-dump.xml" )
    local( "./uploadDump.py ~/Documents/FluffyHomeData/dump_wind_alberta-highasakite-time_2013_108.xml" )



    
