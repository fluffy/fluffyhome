
from fabric.api import *

@task
@hosts('fh4.fluffyhome.com')
def deploy():
    """ Get the code on report host """
    build()
    run( "sudo apache2ctl stop" )
    run( "sudo supervisorctl stop celery" )
    run( "cd src/fluffyhome; git pull" );
    run( "cd src/fluffyhome/energygraph; sudo pip install -q -r requirements.txt ");
    run( "cd src/fluffyhome/; ./manage.py syncdb ");
    #run( "cd src/fluffyhome/; ./manage.py migrate store ");
    run( "cd src/fluffyhome/; ./manage.py collectstatic -v 1 --noinput");
    run( "sudo redis-cli -n 0 flushdb" )
    run( "sudo supervisorctl reload" )
    run( "sudo supervisorctl restart celery" )
    run( "sudo apache2ctl restart" )


@task
@hosts('fh4.fluffyhome.com')
def deployServer():
    """ Setup a new server """
    #run( "sudo apt-get -y install ufw" )
    #run( "sudo ufw default deny" )
    #run( "sudo ufw logging on" )
    #run( "sudo ufw allow ssh/tcp" )
    #run( "sudo ufw limit ssh/tcp" )
    #run( "sudo ufw allow http/tcp" )
    #run( "echo y | sudo ufw enable" )

    #sudo( 'echo "fluffy ALL = NOPASSWD: ALL"  > /etc/sudoers.d/cullen' )
    #sudo( 'echo "fluffy ALL=(postgres) NOPASSWD: ALL"  >> /etc/sudoers.d/cullen' )
    #sudo( "chmod 0440 /etc/sudoers.d/cullen" )

    #run( "sudo apt-get -y install fail2ban" )
    #run( "sudo apt-get -y install logcheck logcheck-database" )

    #run( "sudo apt-get -y install emacs23-nox git-core build-essential gcc tcsh" )
    #run( "sudo apt-get -y install apache2" )

    #run( "sudo apt-get -y install python python-dev python-setuptools" )
    #run( "sudo easy_install pip" )
    #run( "sudo pip install virtualenv virtualenvwrapper" )
    #run( "sudo pip install pytz" )

    #run( "sudo apt-get -y install postgresql python-psycopg2 postgresql-contrib libpq-dev" )
    #run( 'psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname=\'fluffy\'" | grep -q 1 || echo "CREATE ROLE fluffy WITH LOGIN ENCRYPTED PASSWORD \'none\';" | sudo -u postgres psql ' )
    #run( "psql -l | grep energygraph | wc -l | grep -q 1  ||  sudo -u postgres createdb -w -O fluffy energygraph" )
 
    #run( "sudo apt-get -y install mongodb" )
    
    #run( "sudo apt-get -y install redis-server" )
    #run( "sudo pip install redis" ) 
    
    #sudo( "apt-get -y install rabbitmq-server" )
    
    #run( "sudo pip install django fabric django-celery" )
    
    #run( "mkdir -p ~/src" )
    #run( "cd ~/src; if [ ! -d fluffyhome ] ; then git clone git@github.com:fluffy/fluffyhome.git ; fi" )
    #run( "cd ~/src/fluffyhome/energygraph; git pull" )

    #run( "cd ~/src/fluffyhome/energygraph; sudo pip install -r requirements.txt " )
    #run( "mkdir -p ~/src/fluffyhome/energygraph/logs" )

    #run( "cd ~/src/fluffyhome/energygraph; if [ ! -f secrets.py ] ; then cat secrets.tmpl | sed -e 's/pwdReplace/none/' > secrets.py ; fi " )

    #run( "cd ~/src/fluffyhome/energygraph; ../manage.py syncdb --noinput" )
    #run( "cd src/fluffyhome/energygraph; ../manage.py collectstatic -v 1 --noinput");


    # TOOD - next one fails if run twice and needs way to set password 
    # run( "cd src/fluffyhome/energygraph; ../manage.py createsuperuser --username=fluffy --email=fluffy@iii.ca --noinput");

    #sudo( "cd /etc/apache2/sites-available; ln -sf /home/fluffy/src/fluffyhome/energygraph/apache.conf fluffyhome" )
    #sudo( "cd /etc/apache2/sites-enabled;  ln -sf ../sites-available/fluffyhome" );

    #run( "cd ~/src/fluffyhome/energygraph; if [ ! -f apache.conf ] ; then cat apache.tmpl | sed -e 's/www\.fluffyhome/fh4.fluffyhome/' > apache.conf ; fi " )

    #sudo( "apache2ctl restart" )

    #sudo( "apt-get -y install supervisor" )
    #sudo( "cd /etc/supervisor/conf.d; ln -sf /home/fluffy/src/fluffyhome/energygraph/supervisor-celery.conf " )
    #sudo( "mkdir -p /var/lib/celery" )
    #sudo( "chmod a+rw /var/lib/celery" )

    # TODO - next two are not workign 
    #sudo( "supervisorctl reload" )
    #sudo( "supervisorctl restart celery" )

    #run( "sudo apache2ctl restart" )

    # TODO - wait some time
    local( "sleep 5" )
    local( "./uploadDump.py ~/Documents/FluffyHomeData/all-dump.xml http://fh4.fluffyhome.com" )

    

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
    local( "redis-cli -n 0 flushdb" );
    local( "../manage.py runserver" );


@task
def loaddata():
    """ Load some test data in local server """
    local( "./uploadDump.py ~/Documents/FluffyHomeData/all-dump.xml" )
    local( "./uploadDump.py ~/Documents/FluffyHomeData/fluffy-dump.xml" )
    local( "./uploadDump.py ~/Documents/FluffyHomeData/dump_wind_alberta-highasakite-time_2013_108.xml" )



    
