import logging
import time

#from celery.task import task

from energygraph.store.views import *

logger = logging.getLogger('energygraph')


#@task() 
def doTask( x , y ):
    logger.debug( "Running doTask in ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ" )


#@task()
def updateHourly(): # /tasks/update/*/*/*/
    logger.info( "Running task updateHourly" )
    doUpdateAllValuesNow()


def updateWindAB4(): #  /tasks/pollWindAB4/ab-52/
    pass

