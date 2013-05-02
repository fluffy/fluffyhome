# Copyright (c) 2013 Cullen Jennings. All rights reserved.

import logging
#from datetime import timedelta
from datetime import datetime
import time
#from sets import Set
from django.db import models
import json
#from django.core.exceptions import ObjectDoesNotExist

#from energygraph.store.cache import *

logger = logging.getLogger('energygraph')


    
class Measurement2(models.Model):
    sensorID   = models.IntegerField() # system wide unique identifer for sensor
    time       = models.IntegerField() # time this messarement was made (seconds since unix epoch)
    integral   = models.FloatField() # integral of value over time up to this meassurment (units * seconds)
    value      = models.FloatField() # value of sensor at time of meassurment (units)
    energy     = models.FloatField() # cumulative energy used in watt seconds (Joules) 
    patchLevel = models.IntegerField() # version that data has been upgraded too 


def findRecentMeasurements( sensorID ):
    now = long( time.time() )
    t = now
    t = t - 36*3600

    query = Measurement2.objects 
    logger.debug("# DB search for findRecentMeasurements" )
    query = query.filter( sensorID = sensorID )
    query = query.filter( time__gt = t )
    query = query.order_by("-time") 
    maxLimit = 30
    p = query.all()[0:maxLimit]
    return p


def findMeasurementBefore( sensorID, utime, msg=None ):
    query = Measurement2.objects
    logger.debug( msg )
    query = query.filter( sensorID = sensorID )
    query = query.filter( time__lte = utime )
    query = query.order_by("-time") 
    prev = None
    try:
        prev = query.all()[0]
    except IndexError:
        prev = None
    return prev


def findMeasurementAfter( sensorID, utime, msg=None ):
    query = Measurement2.objects
    logger.debug( msg )
    query = query.filter( sensorID = sensorID )
    query = query.filter( time__gte =  utime )
    query = query.order_by("time") 
    next = None
    try:
        next = query.all()[0]
    except IndexError:
        next = None
    return next


def findMeasurementsBetween( sensorID, start, end ):
    query = Measurement2.objects 
    logger.debug("# DB search for findMeasurementsBetween" )
    query = query.filter( sensorID = sensorID )
    query = query.filter( time__gte =  start )
    query = query.filter( time__lt = end )
    query = query.order_by("-time")

    maxLimit = 13000
    p = query.all()[0:maxLimit]

    if len(p) == maxLimit:
        logger.error("findMeasurementsBetween hit max entires of %d "%( len(p) ) )
        c = query.count(100000)
        logger.error("count is %d which is bigger than %d"%( c, maxLimit ) )
        assert c <= maxLimit , "Too many meassurments for this day %d > max of %d"%(c,maxLimit)
        return None
    
    return p


def saveMeasurement( m ):
    m.save()


def thinMeasurements( sensorID, t ):
    # make so at interval from t  - oneHour to t, there is only one measurement (the last)

    assert False, "Removed this no USE "
    
    query = Measurement2.objects 
    logger.debug("# DB search for thinMeasurements" )
    query = query.filter( sensorID = sensorID )
    query = query.filter( time__gt = t-3600 )
    query = query.filter( time__lte = t )
    query = query.order_by("-time") 
    p=query.run( deadline=20, offset=1, batch_size=100, keys_only=True)

    #i=0
    #for x in p:
    #    logger.debug( "found one to delete %d"%i )
    #    db.delete( x )
    #    i = i+1
    #    if i%50 == 0 :
    #        logger.debug( "Deleted %d measurements in thining and still going"%i )
    #logger.debug( "Deleted %d measurements in thining"%i )
    
    futures = db.delete_async( p )
    futures.get_result()
