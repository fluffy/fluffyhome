
from fabric.api import *


def production():
    """Production server settings"""
    #env.settings = 'production'
    #env.user = 'fluffy'
    #env.path = '/home/%(user)s/sites/myproject' % env
    env.hosts = ['fh3.fluffyhome.com']
    #config.fab_hosts = ['fh3.fluffyhome.com']
    #config.repo = "fluffyhome"
    #config.parent = "origin"
    #config.brnach = "master"


def deploy():
    """ Get the code on report host """
    # pull git
    run( "cd src/fluffyhome; git pull" );
    # install requiremtns
    # migrate DB
    # resttar Supervisor
    # restart celery
    # restart appache 



