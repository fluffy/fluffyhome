# Copyright (c) 2013 Cullen Jennings. All rights reserved.

import os
import sys
import urlparse
import logging

#from datetime import timedelta
from datetime import datetime
import time

from django.db import models
import json

from pymongo import MongoClient
from pymongo import ASCENDING, DESCENDING

#from energygraph.store.cache import *

logger = logging.getLogger('energygraph')


class Mongo:
    """ class to wrap the connection to MOngo DB """
    client = None 
    db = None 
    collection = None 

    def __init__( self ):
        self.client = None
        
    def connect( self ):
        url = "mongo://localhost:27017"
        try:
            url = os.environ['MONGO_URL'] 
        except KeyError:
            pass
        print "MONGO_URL = ", url

        urlparse.uses_netloc.append('mongo')
        url = urlparse.urlparse( url )
        assert url.hostname is not None, "Problem with Mongo URL"
        
        self.client = MongoClient(  host=url.hostname, port=url.port)
        assert self.client is not None, "Failed to connect to Mongo server"

        self.db = self.client['energygraph']
        assert self.db is not None, "Failed to connect to Mongo energygraph DB"

        self.collection = self.db['measurements']
        assert self.collection is not None, "Failed to connect to measurement collection"

        doc = self.db.version.find_one();
        dbVersion = 1
        if ( doc == None) or ( not 'version' in doc ) or ( doc['version'] != dbVersion ):
            # wrong version of DB - need to create
            logger.info("Setting up mongo DB to version %d"%dbVersion )

            self.collection.ensure_index( [ ("sensorID",DESCENDING), ("time",DESCENDING) ] );
            self.collection.ensure_index( [ ("sensorID",DESCENDING), ("time",ASCENDING) ] );
            
            self.db.version.save( { 'version': dbVersion } )


mongo = Mongo()


    
class Measurement2(models.Model):
    sensorID   = models.IntegerField() # system wide unique identifer for sensor
    time       = models.IntegerField() # time this messarement was made (seconds since unix epoch)
    integral   = models.FloatField() # integral of value over time up to this meassurment (units * seconds)
    value      = models.FloatField() # value of sensor at time of meassurment (units)
    energy     = models.FloatField() # cumulative energy used in watt seconds (Joules) 
    patchLevel = models.IntegerField() # version that data has been upgraded too 


def findRecentMeasurements( sensorID ):
    ''' Finds the 30 most recent measurements in the last 36 hours '''
    if mongo.client is None:
            mongo.connect()

    now = long( time.time() )
    t = now - 36*3600
    maxLimit = 30

    filter = { 'sensorID': long(sensorID), 'time' :{'$lte':long(now),'$gte':long(t)} }
    docs = mongo.collection.find( filter ).sort( 'time', DESCENDING ).limit(maxLimit)

    ret = []
    for doc in docs:
        #logger.debug( "found doc = %s"%doc )
        m = Measurement2()
        m.sensorID = doc[ 'sensorID' ]
        m.time = doc[ 'time' ]
        m.integral = doc[ 'integral' ]
        m.value = doc[ 'value' ]
        m.energy = doc[ 'energy' ]
        m.patchLevel = doc[ 'patchLevel' ]

        ret.append( m ) 
    
    return ret


def findMeasurementBefore( sensorID, utime, msg=None ):
    logger.debug( msg )
    if mongo.client is None:
            mongo.connect()

    filter = { 'sensorID': long(sensorID), 'time' :{'$lte':long(utime)} }
    docs = mongo.collection.find( filter ).sort( 'time', DESCENDING ).limit(1)

    ret = None
    for doc in docs:
        #logger.debug( "found doc = %s"%doc )
        ret = Measurement2()
        ret.sensorID = doc[ 'sensorID' ]
        ret.time = doc[ 'time' ]
        ret.integral = doc[ 'integral' ]
        ret.value = doc[ 'value' ]
        ret.energy = doc[ 'energy' ]
        ret.patchLevel = doc[ 'patchLevel' ]
    
    return ret


def findMeasurementAfter( sensorID, utime, msg=None ):
    logger.debug( msg )
    if mongo.client is None:
        mongo.connect()
            
    filter = { 'sensorID': long(sensorID), 'time' :{'$gte':long(utime)} }
    docs = mongo.collection.find( filter ).sort( 'time', ASCENDING ).limit(1)

    ret = None
    for doc in docs:
        #logger.debug( "found doc = %s"%doc )
        ret = Measurement2()
        ret.sensorID = doc[ 'sensorID' ]
        ret.time = doc[ 'time' ]
        ret.integral = doc[ 'integral' ]
        ret.value = doc[ 'value' ]
        ret.energy = doc[ 'energy' ]
        ret.patchLevel = doc[ 'patchLevel' ]
    
    return ret




def findMeasurementsBetween( sensorID, start, end ):
    logger.debug("# DB search for findMeasurementsBetween" )
    if mongo.client is None:
            mongo.connect()

    maxLimit = 13000 # TODO - remove  - this was a GAE limit 

    filter = { 'sensorID': long(sensorID), 'time' :{'$lt':long(end),'$gte':long(start)} }
    docs = mongo.collection.find( filter ).sort( 'time', DESCENDING ).limit(maxLimit)

    ret = []
    for doc in docs:
        #logger.debug( "found doc = %s"%doc )
        m = Measurement2()
        m.sensorID = doc[ 'sensorID' ]
        m.time = doc[ 'time' ]
        m.integral = doc[ 'integral' ]
        m.value = doc[ 'value' ]
        m.energy = doc[ 'energy' ]
        m.patchLevel = doc[ 'patchLevel' ]

        ret.append( m ) 
    
    return ret



def saveMeasurement( m ):
    # m.save()

    if mongo.client is None:
            mongo.connect()

    record = { 'sensorID': long(m.sensorID),
               'time': long(m.time),
               'patchLevel': long(m.patchLevel),
               'integral': float( m.integral ),
               'value': float( m.value ),
               'energy': float( m.energy ) }

    mongo.collection.insert( record )

    


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
