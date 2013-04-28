import logging
import time
from celery.task.schedules import crontab  
from celery.decorators import periodic_task  
  
from celery.task import task

from energygraph.store.views import *

logger = logging.getLogger('energygraph')


@periodic_task(run_every=crontab(hour="*", minute="25,55", day_of_week="*"))  
def taskUpdateHourly(): # /tasks/update/*/*/*/
    logger.info( "Running task updateHourly" )
    doUpdateAllValuesNow()
    

#@periodic_task(run_every=crontab(minute="*/5")) # every 5 minutes
def taskShowAllWindSensors(): # refresh the wind cache 
     doShowAllWindSensors()


#@periodic_task(run_every=crontab(minute="*/10")) # every 5 minutes
#@periodic_task( run_every=crontab(minute="*") ) 
#def taskPollRedDeer(): # refresh the wind cache 
#     doPollWindAB2( 'red-deer', None )   # AMA has removed weather information 


@periodic_task(run_every=crontab(minute="*/5")) # every 5 minutes
def taskPollKiteRanch(): # refresh the wind cache 
     doPollWindAB3( 'highasakite', None )  


@periodic_task( run_every=crontab(minute="*/10") ) 
def taskPollCalgaryAirport(): # refresh the wind cache 
     doPollWindAB4( 'ab-52', None )  


@periodic_task( run_every=crontab(minute="*/10") ) 
def taskPollRedDeerAirport(): # refresh the wind cache 
     doPollWindAB4( 'ab-29', None )  


@periodic_task( run_every=crontab(minute="*/10") ) 
def taskPollLethbrideAirport(): # refresh the wind cache 
     doPollWindAB4( 'ab-30', None )  

