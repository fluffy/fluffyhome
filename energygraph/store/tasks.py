import logging
import time
from celery.task.schedules import crontab  
from celery.decorators import periodic_task  
  
from celery.task import task

from energygraph.store.views import *

logger = logging.getLogger('energygraph')


@periodic_task(run_every=crontab(hour="*", minute="25,55", day_of_week="*"))  
def taskUpdateHourly(): # /tasks/update/*/*/*/
    logger.info( "Running task taskUpdateHourly" )

    now = long( time.time() )
    now = now - now % 3600
    goBack = 3*3600 # TODO - how far in past should this go

    startTime = now - goBack
    endTime = now
    
    doUpdateAllValuesNow( startTime, endTime )
     

#@periodic_task(run_every=crontab(minute="*/5")) # every 5 minutes
def taskShowAllWindSensors(): # refresh the wind cache 
    logger.info( "Running task taskShowAllWindSensors" )
    doShowAllWindSensors()


@periodic_task(run_every=crontab(minute="*/5")) # every 5 minutes
def taskPollKiteRanch(): # refresh the wind cache 
    logger.info( "Running taskPollKiteRanch " )
    doPollWindAB3( 'highasakite' )  


@periodic_task( run_every=crontab(minute="*/10") ) 
def taskPollCalgaryAirport(): # refresh the wind cache 
    logger.info( "Running taskPollCalgaryAirport" )
    doPollWindAB4( 'ab-52' )  


@periodic_task( run_every=crontab(minute="*/10") ) 
def taskPollRedDeerAirport(): # refresh the wind cache 
    logger.info( "Running task taskPollRedDeerAirport" )
    doPollWindAB4( 'ab-29' )  


@periodic_task( run_every=crontab(minute="*/10") ) 
def taskPollLethbrideAirport(): # refresh the wind cache 
    logger.info( "Running task taskPollLethbrideAirport" )
    doPollWindAB4( 'ab-30' )  


@periodic_task(run_every=crontab(minute="*/10")) # every 10 minutes
def taskPollChestermere(): # refresh the wind cache 
     doPollWindAB1( '1_10' )  


@periodic_task(run_every=crontab(minute="*/10")) # every 10 minutes
def taskPollGleichen(): # refresh the wind cache 
     doPollWindAB1( '1_14' )


@periodic_task(run_every=crontab(minute="*/10")) # every 10 minutes
def taskPollGranum(): # refresh the wind cache 
     doPollWindAB1( '2_08' )


@periodic_task(run_every=crontab(minute="*/10")) # every 10 minutes
def taskPollCanmore(): # refresh the wind cache 
     doPollWindAB1( '1_02' )


@periodic_task(run_every=crontab(minute="*/10")) # every 10 minutes
def taskPollMonarch(): # refresh the wind cache 
     doPollWindAB1( '3_08b' )  

