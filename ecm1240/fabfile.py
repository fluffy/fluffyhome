
from fabric.api import *

# note serial drivers do not work on osx 10.8 so can not move to mini50

@task
@hosts('fluffymac32.fluffyhome.com')
def deploy():
    local( "git commit --allow-empty -a -m 'update from build' " );
    local( "git push" );
    run( "cd ~/src/fluffyhome; git pull " );
    run( "cd ~/src/fluffyhome/ecm1240; make clean ; make  " );
    run( "cd ~/src/fluffyhome/ecm1240; sudo make install-fluffy " );
    


