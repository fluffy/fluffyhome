
from fabric.api import *

@task
@hosts('fh3.fluffyhome.com')
def deploy():
    """ Get the code on report host """
    run( "cd src/fluffyhome; git pull" );
    run( "cd src/fluffyhome/energygraph; sudo pip install -q -r requirements.txt ");
    run( "cd src/fluffyhome/; ./manage.py syncdb ");
    run( "sudo supervisorctl reload" )
    run( "sudo supervisorctl restart celery" )
    run( "sudo apache2ctl restart" )



