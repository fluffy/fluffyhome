
from fabric.api import *

@task
@hosts('fluffymini50.fluffyhome.com')
def deploy():
    run( "cd ~/src/fluffyhome; git pull " );
    run( "cd ~/src/fluffyhome/ecm1240; make clean ; make  " );
    run( "cd ~/src/fluffyhome/ecm1240; sudo make install-fluffy " );
    


