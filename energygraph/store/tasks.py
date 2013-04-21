import logging
import time
from celery.task.schedules import crontab  
from celery.decorators import periodic_task  
  
from celery.task import task

from energygraph.store.views import *

logger = logging.getLogger('energygraph')


@task() 
def doTask( x , y ):
    logger.debug( "Running doTask in ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ" )


@task()
def updateHourly(): # /tasks/update/*/*/*/
    logger.info( "Running task updateHourly" )
    doUpdateAllValuesNow()


def updateWindAB4(): #  /tasks/pollWindAB4/ab-52/
    pass


# this will run every minute
@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))  
def testTaskOne():      
    print "firing test task"         
