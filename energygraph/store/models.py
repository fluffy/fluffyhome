# Copyright (c) 2010 - 2013 Cullen Jennings. All rights reserved.

import logging
from datetime import timedelta
from datetime import datetime
import time
#from sets import Set
from django.db import models
import json
from django.core.exceptions import ObjectDoesNotExist

from energygraph.store.cache import *
from energygraph.store.modelMeasurement import *

logger = logging.getLogger('energygraph')


def getPatchLevel():
    return 3


class Sensor(models.Model):
    sensorID = models.IntegerField(primary_key=True) # unique interger ID for this sensor 
    sensorName = models.CharField(max_length=64) # For a given user, this is a unique name used in URIs

    label = models.CharField(max_length=128) # human readable, changable, display name
    userID = models.IntegerField() # user that owns this sensor 

    public = models.BooleanField() # data is public 
    hidden = models.BooleanField() # don't show the sensor on main displays of data 
    ignore = models.BooleanField() # don't include sensor in calculations  
    groupTotal = models.BooleanField() # don't show the sesnsor on main displays of data 
    killed = models.BooleanField() # mark this true to effetively delete a sensor

    category = models.CharField( max_length=15,
                                 choices=[ ("Group","Group"), ("Sensor","Sensor") ] )
                                
    type = models.CharField( max_length=15,
                             choices=[ ("None","None"), ("Electricity","Electricity"), ("Gas","Gas"), ("Water","Water") ] )
                                                    
    units = models.CharField (max_length=10,
                              choices=[("None","None"),("V","V"),("W","W"),("C","C"),("F","F"),("lps","lps"),("A","A"),("%","%"),("RH%","RH%"),("Pa","Pa"),("km/h","km/h"),("m/s","m/s")] ) #,'k' 'Ws' #TODO fix, degC and degF
    
    unitsWhenOn = models.CharField(max_length=10, choices=[("None","None"),("W","W"),("lps","lps")]) 

    displayMin = models.FloatField() 
    displayMax = models.FloatField() 

    inGroup = models.IntegerField() # group this sensors is in

    watts = models.FloatField() # TODO depricate this and use valueWhenOn
    valueWhenOn = models.FloatField() 
    threshold = models.FloatField() 

    maxUpdateTime = models.FloatField() # max time for update before sensor is considered "broken"

    def __unicode__(self):
        user = findUserNameByID( self.userID )
        return u'%s %s: %s' % (user,self.sensorName,self.label)

    
globalSensorMetaStore = {}
globalSensorMetaStoreEpoch = 0

def findSensorMetaByID(sensorID, callFrom=None):
    global globalSensorMetaStore
    global globalSensorMetaStoreEpoch

    epoch = getUserSettingEpochBySensorID( sensorID )
    assert epoch > 0 
    assert (type( sensorID ) is long) or (type( sensorID ) is int), "Wrong type of %s "%type( sensorID )
    
    if globalSensorMetaStoreEpoch != epoch:
        globalSensorMetaStoreEpoch = epoch
        globalSensorMetaStore = {}

    if sensorID in globalSensorMetaStore:
        return globalSensorMetaStore[sensorID]

    #logger.debug( "In findSensorMetaByID sensorID=%s"%sensorID )
    assert  long( sensorID ) > 0 , "Problem with sensorID=%s"%sensorID

    logger.debug( 'findSensorMetaByID:%d/%d'%(epoch,sensorID) ) 
    id = memcache.get( 'findSensorMetaByID:%d/%d'%(epoch,sensorID) ) 
    if id != None:
        id = json.loads( id )
        globalSensorMetaStore[sensorID] = id
        return id

    if callFrom is not None:
        logger.debug( "   calling findSensor from findSensorMetaByID from %s"%callFrom )
    else:
        logger.debug( "   calling findSensor from findSensorMetaByID" )

    sensor = findSensor( sensorID , "findSensorMetaByID" )
    assert sensor is not None
    if sensor.units is None:
        sensor.units = ""

    ret = { 'category': sensor.category , 
            'units': sensor.units ,
            'watts': sensor.watts ,
            'valueWhenOn': sensor.valueWhenOn ,
            'unitsWhenOn': sensor.unitsWhenOn ,
            'threshold': sensor.threshold ,
            'maxUpdateTime': sensor.maxUpdateTime,
            'label':  sensor.label ,
            'userID': sensor.userID,
            'sensorName': sensor.sensorName,
            'type': sensor.type,
            'ignore' : sensor.ignore,
            'killed' : sensor.killed, 
            'hidden' : sensor.hidden, 
            'groupTotal' : sensor.groupTotal,
            'inGroup' : sensor.inGroup }

    globalSensorMetaStore[sensorID] = ret
    memcache.put( 'findSensorMetaByID:%d/%d'%(epoch,sensorID), json.dumps( ret ) , 24*3600 )
    return ret


def getSensorUserIDByID(sensorID):
    assert sensorID > 0, "Can't lookup a sensorID of %s "%sensorID
    meta = findSensorMetaByID(sensorID,"getSensorUserIDByID")
    userID = meta['userID']
    assert userID > 0
    return userID


def getSensorCategoryByID(sensorID):
    assert sensorID > 0, "Can't lookup a sensorID of %s "%sensorID
    meta = findSensorMetaByID(sensorID,"getSensorCategoryByID")
    userID = meta['category']
    assert userID > 0
    return userID


def getSensorLabelByID(sensorID):
    assert sensorID > 0 , "Can't lookup a sensorID of %s "%sensorID
    meta = findSensorMetaByID(sensorID,"getSensorLabelByID")
    label = meta['label']
    assert label is not None
    return label


def getSensorNamelByID(sensorID):
    assert sensorID > 0, "Can't lookup a sensorID of %s "%sensorID
    meta = findSensorMetaByID(sensorID,"getSensorNamelByID")
    name = meta['sensorName']
    assert name is not None
    return name


def getSensorUnitsByID(sensorID):
    assert sensorID > 0, "Can't lookup a sensorID of %s "%sensorID
    meta = findSensorMetaByID(sensorID,"getSensorUnitsByID")
    assert meta is not None
    units = meta['units']
    assert units is not None, "Problem with units in sensor meta %s"%meta
    return units


def findGroupPower( sensorID, type, ignoreList ):
    sum = 0.0

    sensorIDs = findAllSensorIDsInGroup( sensorID , "findGroupPower" )
    for sensorID in sensorIDs:
        if sensorID not in ignoreList:
            ignoreList.add( sensorID )
            assert sensorID > 0 , "Problem with sensor %s"%sensor
            meta = findSensorMetaByID( sensorID , "findGroupPower" )
            if ( meta['ignore'] != True ) and ( meta['killed'] != True ) and (meta['groupTotal'] != True ):
                if ( type=="None") or ( type == meta['type'] ) or ( meta['type'] == "None" ):
                    v = findSensorPower( sensorID , type , ignoreList )
                    if v == v : # nan 
                        assert v >= 0.0 
                        sum += v
    return sum



def findGroupWater( sensorID, type, ignoreList ):
    sum = 0.0

    sensorIDs = findAllSensorIDsInGroup( sensorID  , "findGroupWater" )
    for sensorID in sensorIDs:
        if sensorID not in ignoreList:
            ignoreList.add( sensorID )
            assert sensorID > 0 , "Problem with sensor %s"%sensor
            meta = findSensorMetaByID( sensorID , "findGroupWater" )
            if ( meta['ignore'] != True ) and ( meta['killed'] != True ) and (meta['groupTotal'] != True ):
                if ( type=="None") or ( type == meta['type'] ) or ( meta['type'] == "None" ):
                    v = findSensorWater( sensorID , type , ignoreList )
                    if v == v: # nan 
                        assert v >= 0.0
                        sum += v
    return sum



def findGroupTotalSensorID( groupID , ignoreList ):
    """ 
    Find the sensorID of a sensor that meassures the groupTotal for this group. 
    returns 0 if none exist 
    """
    epoch = getUserSettingEpochBySensorID( groupID )
    logger.debug( 'findGroupTotalSensorID:%d/%d'%(groupID,epoch) ) 
    id = memcache.get( 'findGroupTotalSensorID:%d/%d'%(groupID,epoch) ) 
    if id != None:
        id = long(id)
        return id

    ret=0
    logger.debug( "Looking for group total sensor" )
    sensorsIDs = findAllSensorIDsInGroup( groupID  , "findGroupTotalSensorID")
    for sensorID in sensorsIDs:
        if sensorID not in ignoreList:
            ignoreList.add( sensorID )
            assert sensorID > 0 , "Problem with sensor %s"%sensor
            meta = findSensorMetaByID( sensorID , "findGroupTotalSensorID" )
            if ( meta['ignore'] != True) and ( meta['killed'] != True ):
                if ( meta['groupTotal'] == True):
                    ret = sensorID
                    break

    memcache.put( 'findGroupTotalSensorID:%d/%d'%(groupID,epoch), ret , 24*3600 )
    return ret


def findSensorPower( sensorID , type="None" ,ignoreList=set() ): #TODO - unify with getSensorPower 
    sensorMeta = findSensorMetaByID( sensorID )
    assert sensorMeta is not None
    ret = 0.0

    value = getSensorValue( sensorID )
    
    if sensorMeta['category'] == "Sensor":
        if (type=="None") or (type==sensorMeta['type']) or (sensorMeta['type']=="None"):
            ret = getSensorPower( sensorID, value )

    if sensorMeta['category'] == "Group":
        groupTotalSensor = findGroupTotalSensorID( sensorID, ignoreList )
        assert groupTotalSensor != None
        if groupTotalSensor != 0:
            x = long(groupTotalSensor)
            assert x != 0
            ret = findSensorPower( groupTotalSensor , type ,ignoreList ) 
        else:
            assert sensorID > 0 , "Problem with senssorid %s"%sensorID
            ret = findGroupPower( sensorID , type , ignoreList )

    #assert ret >= 0.0
    return ret


def findSensorWater( sensorID , type="None" , ignoreList=set() ): #TODO - unify with getSensorPower 
    sensorMeta = findSensorMetaByID( sensorID )
    assert sensorMeta is not None
    ret = 0.0

    if sensorMeta['category'] == "Sensor":
        if (type=="None") or (type==sensorMeta['type']) or (sensorMeta['type']=="None"):
            if ( sensorMeta['units'] == "lps" ):
                ret = getSensorValue( sensorID )

    if sensorMeta['category'] == "Group":
        groupTotalSensor = findGroupTotalSensorID( sensorID , ignoreList )
        assert groupTotalSensor != None
        if groupTotalSensor != 0:
            x = long(groupTotalSensor)
            assert x != 0
            ret = findSensorWater( groupTotalSensor , type ,ignoreList ) 
        else:
            assert sensorID > 0 , "Problem with sensor id %s"%sensorID
            ret = findGroupWater( sensorID , type ,ignoreList  )

    #assert ret >= 0.0
    return ret



def findAllResourceSensors( userID , inGroupID=None ): #TODO  cache 
    assert userID > 0

    query = Sensor.objects
    logger.debug("# DB search for findAllResourceSensors" )
    query = query.filter( userID = userID )
    sensors = query.all()

    mySet = set()
    if inGroupID is not None:
        assert inGroupID > 0 , "failed with inGroupID='%s'"%inGroupID
        mySet.add( inGroupID )
        done = False
        while not done:
            done = True
            for s in sensors: # if this sensor belongs to a group in the set, then add it and keep going 
                if s.sensorID not in mySet:
                    if s.inGroup in mySet:
                        mySet.add( s.sensorID )
                        done = False
    else:
        for s in sensors:
            mySet.add( s.sensorID )

    ret = []
    for sensor in sensors:
        if (sensor.killed != True) and (sensor.ignore != True) and ( sensor.sensorID in mySet ):
            if sensor.category == "Sensor" and sensor.groupTotal != True :
                if( (sensor.units == "W") or  (sensor.units == "lps") or  (sensor.units == "lpm") or
                    (sensor.units == "%" and sensor.unitsWhenOn == "W" and sensor.valueWhenOn > 0.0 ) or
                    ( (sensor.units == "C" or sensor.units == "F") and sensor.unitsWhenOn == "W" and sensor.valueWhenOn > 0.0 ) ):
                    ret.append( { 'id':sensor.sensorID,
                                  'name':sensor.sensorName,
                                  'label':sensor.label, 
                                  'type':sensor.type,
                                  'group':False } )
                
            if sensor.category == "Group":
                ret.append( { 'id':sensor.sensorID,
                              'name':sensor.sensorName,
                              'label':sensor.label,
                              'type':sensor.type,
                              'group':True } )

    return ret


def findAllNonGroupSensors( ):
    query = Sensor.objects
    logger.debug("# DB search for findAllResourceSensors" )
    sensors = query.all()

    ret = []
    for sensor in sensors:
        if sensor.category != "Group":
            ret.append( { 'id':sensor.sensorID,
                          'name':sensor.sensorName,
                          'label':sensor.label,
                          'type':sensor.type,
                          'userID':sensor.userID,
                          'userName':findUserNameByID(sensor.userID),
                          'group':False } )

    return ret


def findAllSensorsInGroup( groupID , calledBy="" ):
    query = Sensor.objects
    logger.debug("# DB search for findAllSensorsInGroup calledby %s "%calledBy )

    query = query.filter( inGroup = groupID )
    sensors = query.all()

    ret = []
    for sensor in sensors:
        if sensor.killed != True:
            ret.append( sensor )

    return ret


def findAllSensorIDsInGroup( groupID , calledBy="" ):
    epoch = getUserSettingEpochBySensorID( groupID )

    logger.debug( 'findAllSensorIDsInGroup:%d/%d'%(epoch,groupID) )
    id = memcache.get( 'findAllSensorIDsInGroup:%d/%d'%(epoch,groupID) )
    if id != None:
        id = json.loads( id )
        return id

    query = Sensor.objects
    logger.debug("# DB search for findAllSensorIDsInGroup calledby %s "%calledBy )
    query = query.filter( inGroup = groupID )
    sensors = query.all()

    ret = []
    for sensor in sensors:
        if sensor.killed != True:
            ret.append( sensor.sensorID )

    memcache.put( 'findAllSensorIDsInGroup:%d/%d'%(epoch,groupID), json.dumps( ret ), 24*3600 )

    logger.debug("findAllSensorIDsInGroup returned for group %s "%( groupID ) )

    return ret


def findAllSensorsByUserID( userID ):
    query = Sensor.objects
    logger.debug("# DB search for findAllSensorsByUserID" )
    query = query.filter( userID = userID )
    sensors = query.all()
    
    ret = []
    for sensor in sensors:
        if sensor.killed != True:
            ret.append( sensor )

    return ret


def findAllSensorsIDsByUserID( userID ):
    epoch = getUserSettingEpochByUserID( userID )

    logger.debug( 'findAllSensorsIDsByUserID:%d/%d'%(epoch,userID) )
    id = memcache.get( 'findAllSensorsIDsByUserID:%d/%d'%(epoch,userID) )
    if id != None:
        id = json.loads( id )
        return id

    query = Sensor.objects
    logger.debug("# DB search for findAllSensorsIDsByUserID" )
    query = query.filter( userID = userID )
    sensors = query.all()

    ret = []
    for sensor in sensors:
        if sensor.killed != True:
            ret.append( sensor.sensorID )

    memcache.put( 'findAllSensorsIDsByUserID:%d/%d'%(epoch,userID), json.dumps(ret), 24*3600 )
    return ret


def findAllGroupsIdNamePairs( userID ):
    ret = []
    query = Sensor.objects
    logger.debug("# DB search for findAllGroupsIdNamePairs" )
    query = query.filter( userID = userID )
    query = query.filter( category = "Group" )
    sensors = query.all()
    for sensor in sensors:
        if not sensor.killed:
            ret.append(  ( int(sensor.sensorID) , sensor.label ) )
    return ret



def findAllSensorIdNamePairs( userID ):
    ret = []
    query = Sensor.objects
    logger.debug("# DB search forfindAllSensorIdNamePairs " )
    query = query.filter( userID = userID )
    query = query.exclude( category = "Group" )
    sensors = query.all()
    for sensor in sensors:
        if not sensor.killed:
            ret.append(  ( sensor.sensorID , sensor.label ) )
    return ret


def findSensor( sensorID , calledBy="" ):
    query = Sensor.objects
    logger.debug("# DB search for findSensor called by %s "%calledBy )
    query = query.filter( sensorID = sensorID )
    sensor = None
    try:
        sensor = query.all()[0]
    except IndexError:
        pass
    return sensor


def sensorExistsByName( sensorName ):
    id = getSensorIDByName( sensorName )
    if id > 0:
        return True
    return False


globalSensorIDBySensorName = {}

def getSensorIDByName( sensorName ):
    global globalSensorIDBySensorName

    if sensorName in globalSensorIDBySensorName:
        id = globalSensorIDBySensorName[sensorName]
        logger.debug( 'getSensorIDByName: found %s in global with id=%d'%(sensorName,id) )
        return id
    
    logger.debug( 'getSensorIDByName:%s'%(sensorName) )
    id = memcache.get( 'getSensorIDByName:%s'%(sensorName) )
    if id != None:
        id = long( id )
        if id != 0:
            globalSensorIDBySensorName[sensorName] = id
            return id

    query = Sensor.objects
    logger.debug("# DB search for getSensorIDByName" )
    query = query.filter( sensorName = sensorName )
    sensor = None
    try:
        sensor = query.all()[0]
    except IndexError:
        pass
    
    ret = 0
    if sensor != None:
        ret = sensor.sensorID
        memcache.put( 'getSensorIDByName:%s'%(sensorName) , ret, 24*3600 )

    if ret != 0:
        globalSensorIDBySensorName[sensorName] = ret

    logger.debug( 'getSensorIDByName: sensorName %s has ID of %d'%(sensorName,ret) )
    return ret 


def findSensorID( userName, sensorName, create=False , createGroup=False ):
    assert userName is not None, "Must pass valid userName" 
    assert sensorName is not None, "Must pass valid sensorName"

    logger.debug( 'sensorID:%s/%s'%(userName,sensorName) )
    id = memcache.get( 'sensorID:%s/%s'%(userName,sensorName) )
    if id != None:
        id = long( id )
        return id

    userID = findUserIdByName( userName )
    if userID == 0:
        return 0

    query = Sensor.objects
    logger.debug("# DB search for findSensorID" )
    query = query.filter( userID=userID )
    query = query.filter( sensorName=sensorName )
    sensor = None
    try:
        sensor = query.all()[0]
    except IndexError:
        pass

    if sensor is not None:
        # put in memcache 
        memcache.put(  'sensorID:%s/%s'%(userName,sensorName), str(sensor.sensorID) , 3600 )
        return sensor.sensorID

    if not create:
        return 0

    sensorID = getNextSensorID()
    assert sensorID != 0

    # create a new sensor record
    logger.debug("# DB create new sensor name=%s, userID=%s, sensorID=%s "%(sensorName, userID, sensorID) )
    sensor = Sensor( sensorName=sensorName, userID=userID, sensorID=sensorID)

    sensor.userID = userID
    sensor.public = True
    sensor.killed = False
    sensor.hidden = False
    sensor.ignore = False
    sensor.label = sensorName
    sensor.groupTotal = False
    
    sensor.watts = 0.0
    sensor.valueWhenOn = 0.0
    sensor.threshold = float( "inf" )
    
    sensor.displayMin = float("-inf")
    sensor.displayMax = float("inf")

    sensor.maxUpdateTime = float("inf")
    
    if createGroup:
        sensor.category = "Group"
    else:
        sensor.category = "Sensor"
        
    if sensorName == "All":
        sensor.category = "Group"
        sensor.label = "All Group"
        sensor.inGroup = 0
    else:
        sensor.inGroup = findSensorID(userName,"All",True)

    sensor.save()
    logger.debug("# DB create new sensor" )
    updateUserSettingsEpoch(userName)

    return sensorID


class AlarmData(models.Model):
    time  = models.IntegerField() # time this messarement was made (seconds since unix epoch)
    crit  = models.IntegerField() # 0=status, 1=info, 2=important, 3=alert 
    notCrit  = models.IntegerField() # set to 1 if crit is 5, 0 otherwise
    alarmID = models.IntegerField()
    eq = models.IntegerField()
    code = models.IntegerField() # todo should be true , and next one too 
    part = models.IntegerField()
    zone = models.IntegerField()
    user = models.IntegerField()
    note = models.CharField(max_length=80)


def addAlarmData( a, eq, c, p, crit, z=None, u=None, note=None ):
    rec = AlarmData()

    rec.time = long( time.time() )
    rec.alarmID = a
    rec.eq = eq
    rec.code = c
    rec.part = p
    rec.crit = crit
    rec.notCrit = 0
    if crit == 5:
        rec.notCrit = 1
    rec.zone = z
    rec.user = u
    rec.note = note 

    logger.debug("saving alarm data account=%d user=%d eq=%d code=%d zone=%d part=%d"
                  %(rec.alarmID, rec.user, rec.eq, rec.code, rec.zone, rec.part) )

    rec.save()
    logger.debug("# DB put for addAlarmData" )


def findRecentAlarmData( alarmID ):
    now = long( time.time() )
    t = now
    t = t - 2*24*60*60

    query = AlarmData.objects 
    logger.debug("# DB search for findRecentAlarmData" )
    query = query.filter( alarmID = alarmID )
    #query = query.exclude( code = 602 ) # can't do this in GAE 
    #query = query.filter( notCrit = 0 ) # filter out stuff where crit = 5 
    query = query.filter( time__gt = t )
    query = query.order_by("-time") 
    p = query.all()[0:100]

    return p


def findAlarmsBetween( alarmID, start, end ):
    query = AlarmData.objects 
    logger.debug("# DB search for findAlarmBetween" )
    query = query.filter( alarmID = alarmID )
    query = query.filter( time__gte =  start )
    query = query.filter( time__lt = end )
    query = query.order_by("-time")

    maxLimit = 10000
    p = query.all()[0:maxLimit]

    if len(p) == maxLimit:
        logger.error("findAlarmBetween hit max entires of %d "%( len(p) ) )
        c = query.count(100000)
        logger.error("count is %d which is bigger than %d"%( c, maxLimit ) )
        assert c <= maxLimit , "Too many alarms for this day %d > max of %d"%(c,maxLimit)
        return None
    
    return p


class SystemData(models.Model):
    nextSensorID = models.IntegerField()
    nextUserID = models.IntegerField()
    twitterConsumerToken  = models.CharField(max_length=80)
    twitterConsumerSecret = models.CharField(max_length=80)
    

def getSystemData():
    query = SystemData.objects
    logger.debug("# DB search for getSystemData" )
    try:
        sys = query.all()[0]
    except IndexError:
        sys = None
        
    if sys is None:
        #create new sys data object 
        sys = SystemData()
        sys.nextSensorID =1
        sys.nextUserID = 1
        sys.twitterConsumerToken = ""
        sys.twitterConsumerSecret = ""
        sys.save()
        logger.debug("# DB create for getSystemData" )
    assert sys != None

    if sys.twitterConsumerToken == None:
        sys.twitterConsumerToken = ""
        sys.twitterConsumerSecret = ""
        sys.save()
        logger.debug("# DB update for getSystemData" )
        
    return sys


def getNextSensorID():
    sys = getSystemData()
    #TODO do as transaction
    id = sys.nextSensorID
    sys.nextSensorID = id +1 
    sys.save()
    logger.debug("# DB put for getNextSensorID" )
    return id


def getNextUserID():
    sys = getSystemData()
    #TODO do as transaction
    id = sys.nextUserID
    sys.nextUserID = id +1 
    sys.save()
    logger.debug("# DB put for getNextUserID" )
    return id


class User(models.Model):
    userID = models.IntegerField(primary_key=True) 
    userName = models.CharField(max_length=80)
    email  = models.CharField(max_length=80,blank=True)
    email2 = models.CharField(max_length=80,blank=True)
    email3 = models.CharField(max_length=80,blank=True)
    sms1   = models.CharField(max_length=80,blank=True)
    twitter = models.CharField(max_length=256,blank=True)
    purlKey = models.CharField(max_length=256,blank=True)
    passwd = models.CharField(max_length=80,blank=True)
    newPwd      = models.CharField(max_length=80,blank=True)
    newPwdAgain = models.CharField(max_length=80,blank=True)
    active = models.BooleanField()
    settingEpoch = models.IntegerField() # this increments each time the setting or sensors change for this user 
    timeZoneOffset = models.FloatField()
    gasCost = models.FloatField()
    elecCost = models.FloatField()
    waterCost = models.FloatField()
    gasCO2 = models.FloatField()
    elecCO2 = models.FloatField()
    twitterAccessToken = models.CharField(max_length=256,blank=True)
    twitterAccessSecret = models.CharField(max_length=256,blank=True)
    twitterTempToken = models.CharField(max_length=256,blank=True)
    twitterTempSecret = models.CharField(max_length=256,blank=True)

    def __unicode__( self ):
        return u'%s'%( self.userName )


def getUserPasswordHash( userName ):
    
    try:
        epoch = getUserSettingEpoch( userName )
    except AssertionError:
         logger.warning( "User %s does not exist"%userName )
         return None

    assert epoch > 0 
    logger.debug( 'getUserPasswordHash:%d/%s'%(epoch,userName)  )
    id = memcache.get( 'getUserPasswordHash:%d/%s'%(epoch,userName)  )
    if id != None:
        id = str( id )
        return id

    user = findUserByName( userName )
    if user is None:
        return None

    ret = user.passwd

    if user.passwd is None:
        user.passed = ""
        user.save()
        return ret
        
    if user.passwd is "": # don't allow empty passwords 
        return None

    memcache.put( 'getUserPasswordHash:%d/%s'%(epoch,userName) ,ret , 24*3600 )
    return ret


def findAllUserNames( ):
    query = User.objects
    logger.debug("# DB search for findAllUserNames" )
    users = query.all()
    ret = []
    for user in users:
        if user.active != False :
            ret.append( user.userName )
    return ret


def createUser( userName , password ):
    id = getNextUserID()
    user = User()

    user.userName = userName
    user.active = True
    user.userID = id

    user.email = ""
    user.email2 = ""
    user.email3 = ""
    user.sms1 = ""
    user.twitter = ""
    user.purlKey = ""

    user.timeZoneOffset = 0
    user.gasCost = 0.0288
    user.elecCost = 0.06889
    user.waterCost = 0.001307
    user.gasCO2 = 0.19
    user.elecCO2 = 0.22

    user.settingEpoch = 1
    user.passwd = password # will not be able to log on till password is set

    twitterAccessToken = ""
    twitterAccessSecret = ""
    
    user.save()
    logger.debug("# DB put for createUser" )

    findSensorID( userName, "All", create=True )
    
    return id
    

def getUserMetaByUserID( userID ):
    epoch = getUserSettingEpochByUserID( userID )
    assert epoch > 0 
    assert epoch != None
    
    logger.debug( 'getUserMetaByUserID:%s/%s'%(epoch,userID) ) 
    id = memcache.get( 'getUserMetaByUserID:%d/%d'%(epoch,userID) ) 
    if id != None:
        #logger.debug( 'json id=%s'%id )
        id = json.loads( id )
        #logger.debug( 'id=%s'%id )
        return id

    user = findUserByID( userID )
    assert user is not None

    ret = {
        "timeZoneOffset":user.timeZoneOffset,
        "gasCost":user.gasCost,
        "elecCost":user.elecCost,
        "waterCost":user.waterCost,
        "gasCO2":user.gasCO2,
        "elecCO2":user.elecCO2,
        "email1":user.email,
        "email2":user.email2,
        "email3":user.email3,
        "sms1":user.sms1
        }

    j = json.dumps( ret )
    #logger.debug( 'ret=%s json=%s'%(ret,j) )
    memcache.put( 'getUserMetaByUserID:%d/%d'%(epoch,userID), j , 24*3600 )
    return ret


def updateUserSettingsEpoch(userName):
    user = findUserByName( userName )
    assert user is not None
    #TODO do as transaction
    if user.settingEpoch is None:
        user.settingEpoch = 0
    user.settingEpoch =  user.settingEpoch + 1 
    user.save()
    logger.debug("# DB put for updateUserSettingsEpoch" )
    memcache.put( 'UserSettingEpoch:%s'%(user.userName) , user.settingEpoch , 24*3600 )
    memcache.put( 'getUserSettingEpochByUserID:%s'%(user.userID) , user.settingEpoch , 24*3600 )


globalUserName=""
globalEpoch=0
globalEpochTime=0

def getUserSettingEpoch(userName):
    global globalUserName
    global globalEpoch
    global globalEpochTime

    now = long(  time.time() )
    #now = now - now%5 # round to lower 5 seconds 

    if globalUserName == userName:
        if globalEpoch > 0:
            if globalEpochTime == now:
                return globalEpoch
            
    logger.debug( 'UserSettingEpoch:%s'%(userName)  )
    id = memcache.get( 'UserSettingEpoch:%s'%(userName)  )
    if id != None:
        ret = long(id)
        globalUserName = userName
        globalEpoch  = ret
        globalEpochTime = now
        return ret

    user = findUserByName( userName )
    assert user is not None
    if user.settingEpoch is None:
        updateUserSettingsEpoch( userName )
        ret = 1
    else:
        ret = user.settingEpoch

    logger.debug("Doing cache set in getUserSettingEpoch userName=%s ret=%d"%(userName,ret) )
    memcache.put( 'UserSettingEpoch:%s'%(userName) , ret , 24*3600 )

    #globalUserName = userName
    #globalEpoch  = ret
    #globalEpochTime = now

    return ret


def getUserSettingEpochByUserID(userID):
    logger.debug( 'getUserSettingEpochByUserID:%s'%(userID)  )
    id = memcache.get( 'getUserSettingEpochByUserID:%s'%(userID)  )
    if id != None:
        return long(id)

    user = findUserByID( userID )
    assert user is not None
    if user.settingEpoch is None:
        updateUserSettingsEpoch( user.userName )
        ret = 1
    else:
        ret = user.settingEpoch
    memcache.put( 'getUserSettingEpochByUserID:%s'%(userID) , ret , 24*3600 )
    return ret



def getUserSettingEpochBySensorID(sensorID):
    return getUserSettingEpoch( findUserNameBySensorID( sensorID ))


globalUserNameBySensorID = {}

def findUserNameBySensorID(sensorID):
    global globalUserNameBySensorID

    if sensorID in globalUserNameBySensorID:
        return globalUserNameBySensorID[sensorID]

    logger.debug( 'findUserNameBySensorID:%d'%(sensorID)  )
    id = memcache.get( 'findUserNameBySensorID:%d'%(sensorID)  )
    if id != None:
        ret = str(id)
        globalUserNameBySensorID[sensorID] = ret
        return ret

    sensor = findSensor( sensorID ,"findUserNameBySensorID" )
    assert sensor is not None
    assert sensor.userID is not None
    assert sensor.userID  > 0

    user = findUserByID( sensor.userID )
    assert user is not None
    assert user.userName is not None
    ret = user.userName

    memcache.put( 'findUserNameBySensorID:%d'%(sensorID) , ret , 24*3600 )
    globalUserNameBySensorID[sensorID] = ret

    return ret



def findUserIDByName( userName ): 
    logger.debug("Looking for user %s"%userName )
    # returns 0 if none found 

    id = None
    logger.debug( 'userID:%s'%(userName) )
    id = memcache.get( 'userID:%s'%(userName) )
    logger.debug( "return id = %s"%id )
    if id != None:
        r = long( id )
        logger.debug( "got a hit r=%s"%r )
        return r

    query = User.objects
    logger.debug("# DB search for findUserIDByName" )
    query = query.filter( userName = userName )
    user = None
    try:
        user = query.all()[0]
    except IndexError:
        pass
    
    if user != None:
        id = user.userID
        logger.debug( "found user ID %d "%id )
        # put in memcache 
        memcache.put( 'userID:%s'%(userName) , str(id) , 24*3600 )
        return id

    return long( 0 )
    

def findUserByName( userName ):
    #query = User.objects
    logger.debug("# DB search for findUserByName" )
    #query = query.filter( 'userName =', userName )
    #user = query.all()[0]
    user = None
    try:
        user = User.objects.get( userName=userName )
    except IndexError:
        pass
    except ObjectDoesNotExist:
        return None
    
    return user


def findUserByID( userID ):
    #query = User.objects
    logger.debug("# DB search for findUserByID" )
    #query = query.filter( 'userID =', userID )
    #user = query.all()[0]
    user = None
    try:
        user = User.objects.get( userID=userID )
    except IndexError:
        pass
    
    assert user is not None
    return user


def findUserNameByID( userID ):
    logger.debug( 'findUserNameByID:%d'%userID )
    val = memcache.get( 'findUserNameByID:%d'%userID )
    if val != None:
        val = str( val )
        return val

    user = findUserByID( userID )
    assert user is not None
    ret = user.userName
    assert ret is not None

    memcache.put( 'findUserNameByID:%d'%userID, ret, 24*3600 )
    return ret


def findUserIdByName( userName ):
    logger.debug( 'findUserIdByName:%s'%userName )
    val = memcache.get( 'findUserIdByName:%s'%userName )
    if val != None:
        val = long( val )
        return val

    user = findUserByName( userName )
    if user is None:
        return 0

    ret = user.userID
    assert ret is not None
    assert (type( ret ) is int) or (type( ret ) is long), "Wrong userID of type %s"%( type(ret) )

    memcache.put( 'findUserIdByName:%s'%userName, ret, 24*3600 )
    return ret




    

def hourlyPatchCount():
    assert False
    level = getPatchLevel()

    sensorID = getSensorIDByName( 'ECM1240-42414-ch2' )
    assert sensorID is not None

    logger.debug("hourlyPatch sensorID = %d"%sensorID )
    
    query = Hourly1.objects
    query = query.filter( patchLevel__lt = level)
    
    #query = query.filter( 'hourOfDay =', 0 )
    #query = query.filter( 'sensorID =', sensorID )
    
    logger.debug("# DB search for hourlyPatchCount" )     
    c = query.count(100000)
    
    logger.info("hourlyPatchCount got %d"%(c) )   
    return c

        
def hourlyPatchFast(): 
    assert False
    level = getPatchLevel()
    maxUpgrade = 1000
    
    query = Hourly1.objects
    query = query.filter( patchLevel__lt = level) 
    logger.debug("# DB search for hourlyPatch" )

    #cursor = memcache.get('hourly_path_cursor_%d_a'%level)
    #if ( cursor ):
    #    query.with_cursor( cursor )
        
    results = query.all()[0:maxUpgrade]

    #cursor = query.cursor()
    #memcache.put('hourly_path_cursor_%d_a'%level,cursor, 2*24*3600 )

    c=0
    patched = set()
    for result in results:
        if result.patchLevel < 3:
            result.patchLevel = level
            result.hourOfDay  = (result.time / 3600) % 24 
            result.hourOfWeek = (result.time / 3600) % (24*7) #added before patchLevel 2 

            patched.add( result )
            logger.debug("Updated result #%d time=%i sensorID=%d"%(c,result.time,result.sensorID) )
            c = c+1
            
    #db.put_async( patched )
    db.put( patched )
    
    logger.info("hourlyPatchFast processed patched %d records"%(c) )   
    return c


def hourlyPatch(): 
    assert False
    maxUpgrade = 50

    level = getPatchLevel()
    sensorID = getSensorIDByName( 'ECM1240-42414-ch2' )

    assert sensorID is not None

    logger.debug("hourlyPatch sensorID = %d"%sensorID )
    
    query = Hourly1.objects
    query = query.filter( patchLevel__lt = level) 
    query = query.filter( sensorID = sensorID )
    #query = query.order_by("time")  # can't do this and do comparison to patchLevel
    logger.debug("# DB search for hourlyPatch" )
    records = query.all()[0:maxUpgrade]

    c=0
    for record in records:
        computeHourlyBySensorID( record.sensorID, record.time )
        c = c+1
        logger.debug("Updated result # %d"%c )
            
    logger.info("hourlyPatch patched %d"%(c) )   
    return c



def getHourlyEnergyTotalByGroupID( groupID, utime ):
    assert groupID > 0
    assert utime > 0 
    
    logger.debug( 'getHourlyEnergyTotalByGroupID:%d/%d'%(groupID,utime) )
    val = memcache.get( 'getHourlyEnergyTotalByGroupID:%d/%d'%(groupID,utime) )
    if val != None:
        val = float( val )
        return val

    gt = findGroupTotalSensorID( groupID , set() )
    if gt != 0:
        ret = getHourlyEnergyBySensorID( gt, utime )
    else:
        sum = 0.0
        sensors = findAllSensorsInGroup( groupID ,"getHourlyEnergyTotalByGroupID" ) #TODO fix form to cache 
        for sensor in sensors:
            if ( sensor.ignore != True ) and ( sensor.killed != True ) and (sensor.groupTotal != True ):
                if sensor.category == "Sensor" :
                    v = getHourlyEnergyBySensorID( sensor.sensorID , utime )
                    if v == v: # nan 
                        assert v >= 0.0 
                        sum += v
                if sensor.category == "Group" :
                    v = getHourlyEnergyTotalByGroupID( sensor.sensorID , utime )
                    if v==v : # nan 
                        assert v >= 0.0 
                        sum += v
        ret = sum

    assert ret >= 0.0
    memcache.put(  'getHourlyEnergyTotalByGroupID:%d/%d'%(groupID,utime), ret, 5*60 )
    return ret


def getHourlyEnergyOtherByGroupID( groupID, utime ):
    assert groupID > 0
    assert utime > 0 
    
    logger.debug( 'getHourlyEnergyOtherByGroupID:%d/%d'%(groupID,utime) )
    val = memcache.get( 'getHourlyEnergyOtherByGroupID:%d/%d'%(groupID,utime) )
    if val != None:
        val = float( val )
        return val

    #logger.debug( "Start getHourlyEnergyOtherByGroupID for group %s"%(getSensorLabelByID( groupID ) ) )

    gt = findGroupTotalSensorID( groupID , set() )
    if gt == 0:
        # no group total found
        return 0.0

    total = getHourlyEnergyBySensorID( gt, utime )

    sum = 0.0
    sensors = findAllSensorsInGroup( groupID , "getHourlyEnergyOtherByGroupID") #TODO fix form to cache 
    for sensor in sensors:
        if ( sensor.ignore != True ) and ( sensor.killed != True ) and (sensor.groupTotal != True ):
            if sensor.category == "Sensor" :
                v = getHourlyEnergyBySensorID( sensor.sensorID , utime )
                #logger.debug("sum sensor in label=%s sum=%f"%( getSensorLabelByID(sensor.sensorID),sum))
                if v == v : # nan
                    if v >= 0.0 :
                        sum += v
                        logger.debug("other added label=%s v=%f to sum=%f"%
                                      (getSensorLabelByID(groupID),v, sum))

            if sensor.category == "Group" :
                v = getHourlyEnergyTotalByGroupID( sensor.sensorID , utime )
                #logger.debug("sum group in label=%s sum=%f"%( getSensorLabelByID(sensor.sensorID),sum))
                if v == v : # nan
                    if v >= 0.0 :
                        sum += v
                        logger.debug("other added group label=%s v=%f to sum=%f"%
                                      (getSensorLabelByID(groupID),v, sum))


    assert total >= 0.0
    assert sum >= 0.0
    ret = total - sum 
    logger.debug("End getHourlyEnergyOtherByGroupID groupid=%d label=%s sum=%f total=%f ret=%f"%(groupID,
                                                                                                 getSensorLabelByID(groupID),
                                                                                                 sum,total,ret))

    if ret < 0.0: # TODO - think about this
        logger.debug("Negative other energy in getHourlyEnergyOtherByGroupID groupid=%d label=%s sum=%f total=%f ret=%f"%
                      (groupID,
                        getSensorLabelByID(groupID),
                        sum,total,ret))
        ret = 0.0 

    assert ret >= 0.0
    memcache.put(  'getHourlyEnergyOtherByGroupID:%d/%d'%(groupID,utime), ret, 5*60 )
    return ret


def getHourlyEnergyBySensorID( sensorID, utime ): # TODO - can we get rid of this
    assert sensorID > 0
    assert utime > 0 ,  "Problem with invalid utime of %d"%utime
    assert utime <= long( time.time() )

    utime = long( utime )
    utime = utime - utime % 3600

    logger.debug( 'getHourlyEnergyBySensorID:%d/%d'%(sensorID,utime) )
    val = memcache.get( 'getHourlyEnergyBySensorID:%d/%d'%(sensorID,utime) )
    if val != None:
        val = float( val )
        return val

    logger.debug("getHourlyEnergyBySensorID: sensorID=%d time=%d hour ago"%( sensorID ,
                                                                              (utime-time.time())/3600.0 ) )
   
    hourly = getHourlyBySensorIDTime( sensorID, utime )
    
    if hourly is None:
        hourly = computeHourlyBySensorID( sensorID , utime )
        
    assert hourly is not None

    assert hourly.energy >= 0.0
    memcache.put(  'getHourlyEnergyBySensorID:%d/%d'%(sensorID,utime), hourly.energy, 24*3600 )
    return hourly.energy



def getHourlyIntegralBySensorID( sensorID, utime ):
    assert sensorID > 0
    assert utime > 0, "Problem with invalid utime of %d"%utime
    assert utime <= long( time.time() )

    logger.debug( 'getHourlyIntegralBySensorID:%d/%d'%(sensorID,utime) )
    val = memcache.get( 'getHourlyIntegralBySensorID:%d/%d'%(sensorID,utime) )
    if val != None:
        val = float( val )
        return val

    utime = long( utime )
    utime = utime - utime % 3600

    hourly = getHourlyBySensorIDTime( sensorID, utime )
    
    if hourly is None:
        hourly = computeHourlyBySensorID( sensorID , utime )

    assert hourly is not None

    memcache.put(  'getHourlyIntegralBySensorID:%d/%d'%(sensorID,utime), hourly.integral, 24*3600 )
    return hourly.integral
  


def computeHourlyBySensorID( sensorID, utime, prev=None, next=None ):
    logger.debug( "In computeHourlyBySensorID sensorid=%d "%(sensorID) )
    assert sensorID > 0
    assert utime > 0
    assert utime <= long( time.time() )

    utime = long( utime )
    utime = utime - utime % 3600

    # find before and after points
    if prev is None:
        prev = findMeasurementBefore(  sensorID, utime,"# DB search for prev computeHourlyBySensorID" )
        
    if next is None:
        next = findMeasurementAfter(  sensorID, utime,"# DB search for next computeHourlyBySensorID " )

    hourly = getHourlyBySensorIDTime( sensorID, utime )
    
    if hourly is None:
        hourly = Hourly1()
        hourly.sensorID = sensorID
        hourly.time = utime 
        meta = findSensorMetaByID( sensorID )
        assert meta is not None
        hourly.userID = meta['userID'] 
        assert hourly.userID > 0 
  
    hourly.hourOfDay  = (hourly.time / 3600) % 24 
    hourly.hourOfWeek = (hourly.time / 3600) % (24*7) 

    hourly.integral = 0.0
    hourly.value = 0.0
    hourly.energy = 0.0
    hourly.groupOtherValue = 0.0
    hourly.groupOtherEnergy = 0.0
    hourly.patchLevel = 0
    
    if patchMeasurement( prev ):
        saveHourly( prev )
        
    if patchMeasurement( next ):
        saveHourly( next )
        
    hourly.patchLevel = getPatchLevel()
    
    if prev is not None:
        hourly.integral = getSensorIntegral(sensorID,utime,prev,next)
        hourly.value = prev.value
        hourly.energy = getSensorEnergy(sensorID,utime,prev,next)

    if getSensorCategoryByID( sensorID ) == "Group":
        hourly.energy = getHourlyEnergyTotalByGroupID(sensorID,utime)
        hourly.groupOtherValue = 0.0 # TODO 
        hourly.value = 0.0 # TODO
        hourly.integral = 0.0 #  TODO ? not clear what this would be 
        hourly.groupOtherEnergy = getHourlyEnergyOtherByGroupID( sensorID, utime )

    logger.debug("# DB put for computeHourlyBySensorID" )
    saveHourly( hourly )

    logger.debug( "hourly integral = %f"%hourly.integral )
    logger.debug( "hourly value = %f"%hourly.value )
    logger.debug( "hourly energy = %f"%hourly.energy )
    if getSensorCategoryByID( sensorID ) == "Group":
        logger.debug( "hourly other = %f"%hourly.groupOtherEnergy )

    return hourly



class KnownIP(models.Model):
    ip       = models.CharField(max_length=80)
    time     = models.IntegerField() # time this messarement was made (seconds since unix epoch)
    sensorID = models.IntegerField() # system wide unique identifer for sensor


def addKnownIP( ip, sensorName=None ):
    sensorID = 0
    if sensorName != None:
        sensorID = getSensorIDByName( sensorName )
        
    if checkKnownIP( ip, sensorID, calledBy="addKnownIP"):
        return

    knownIP = KnownIP( ip=ip, sensorID=sensorID , time=long( time.time() ) )
    knownIP.save()
    logger.debug("# DB create new KnownIP for ip=%s sensor=%s"%(ip,sensorName) )
   
    return


globalKnownIP = {}

def checkKnownIP( ip, sensorID=0, calledBy=""):
    global globalKnownIP 
    # cache this in local mem and check that first 
    if ip in globalKnownIP:
        return True
     
    cachekey = "checkKnownIP:%s/%d"%(ip,sensorID)
    logger.debug( cachekey) 
    id = memcache.get( cachekey ) 
    if id != None:
        globalKnownIP[ip] = True
        return True
 
    query = KnownIP.objects
    logger.debug("# DB search for KnownIP=%s sensorID=%d calledby=%s "%(ip,sensorID,calledBy) )
    query = query.filter( ip = ip )
    query = query.filter( sensorID = sensorID )
    query = query.order_by("-time") 
    knownIP = None
    try:
        knownIP = query.all()[0]
    except IndexError:
        pass
    
    if knownIP == None:
        return False

    memcache.put( cachekey, True , 24*3600 )
    globalKnownIP[ip] = True
    return True


def findAllKnownIP():
    query = KnownIP.objects
    logger.debug("# DB search for findAllKnownIP" )
    query = query.filter( sensorID = 0 )
    query = query.order_by("-time") 
    ips = query.all()

    ret = set()
    for ip in ips:
        ret.add( ip.ip )
    return ret


def findIPforSensorID( sensorID ):
    query = KnownIP.objects
    logger.debug("# DB search for findAllKnownIP" )
    query = query.filter( sensorID = sensorID )
    query = query.order_by("-time") 
    ips = query.all()

    ret = None
    for ip in ips:
        ret = ip.ip 
    return ret
   
    


def patchMeasurement( m ):
    if ( m is None ):
        return False
    
    if ( m.patchLevel is not None ) and ( m.patchLevel == getPatchLevel() ):
        return False

    if m.patchLevel is None:
        m.patchLevel = 0

    level = getPatchLevel()
    
    if ( m.patchLevel < 1 ) and ( level >= 1 ): # This is a patch level 1 change 
        if m.sensorID == getSensorIDByName( 'ZB-0013A2004052-ch1' ):
            m.integral = m.integral * 6.389
            m.value = m.value * 6.389

    if ( m.patchLevel < 2 ) and ( level >= 2 ): # This is a patch level 2 change 
        if (      ( m.sensorID == getSensorIDByName( 'ECM1240-42340-ch1' ) )
               or ( m.sensorID == getSensorIDByName( 'ECM1240-42340-ch2' ) )
               or ( m.sensorID == getSensorIDByName( 'ECM1240-42414-ch1' ) )
               or ( m.sensorID == getSensorIDByName( 'ECM1240-42414-ch2' ) ) ):
            raw = int( m.integral )
            corr = raw
            if ( (raw>>31)&1 ):
                corr = raw + (1<<32)
            m.integral = float( corr )
            m.energy = m.integral

    if ( m.patchLevel < 3 ) and ( level >= 3 ): # This is a patch level 3 change
        pass # nothing to do - this patch upgraded the hourOfWeek handled elswhere 
 
    m.patchLevel = getPatchLevel()
    return True
    


    
globalLastMeasurementTime = {}
globalLastMeasurementValue = {}
globalLastMeasurementEnergy = {}
globalLastMeasurementIntegral = {}
globalLastMeasurementCacheTime = 0

def getSensorValue( sensorID ):
    global globalLastMeasurementTime
    global globalLastMeasurementValue
    global globalLastMeasurementEnergy 
    global globalLastMeasurementIntegral
    global globalLastMeasurementCacheTime
    
    now = long( time.time() )
    if (now - globalLastMeasurementCacheTime) > 15:
        globalLastMeasurementTime = {}
        globalLastMeasurementValue = {}
        globalLastMeasurementEnergy = {}
        globalLastMeasurementIntegral = {}
        globalLastMeasurementCacheTime = now

    if sensorID in globalLastMeasurementValue:
        return globalLastMeasurementValue[sensorID]

    logger.debug( 'lastMeasurementValue:%d'%sensorID )
    val = memcache.get( 'lastMeasurementValue:%d'%sensorID )
    if val != None:
        ret = float(val)
        globalLastMeasurementValue[sensorID] = ret
        return ret

    p = findMeasurementBefore( sensorID, now, "# DB search for getSensorValue for sensor %s"%( getSensorNamelByID(sensorID) ) )
    
    ret = 0.0
    if p is not None:
        ret = float( p.value )

    memcache.put(  'lastMeasurementValue:%d'%sensorID, ret , 24*3600 )
    return ret


def getSensorLastTime( sensorID ):
    global globalLastMeasurementTime
    global globalLastMeasurementValue
    global globalLastMeasurementEnergy 
    global globalLastMeasurementIntegral
    global globalLastMeasurementCacheTime
    now = long( time.time() )
    if (now - globalLastMeasurementCacheTime) > 15:
        globalLastMeasurementTime = {}
        globalLastMeasurementValue = {}
        globalLastMeasurementEnergy = {}
        globalLastMeasurementIntegral = {}
        globalLastMeasurementCacheTime = now

    if sensorID in globalLastMeasurementTime:
        return globalLastMeasurementTime[sensorID]

    logger.debug( 'lastMeasurementTime:%d'%sensorID )
    val = memcache.get( 'lastMeasurementTime:%d'%sensorID )
    if val != None:
        ret = long( val )
        globalLastMeasurementTime[sensorID] = ret
        return ret

    p = findMeasurementBefore( sensorID, now, "# DB search getSensorLastTime " )
    
    ret = 0
    if p is not None:
        ret = long( p.time )

    memcache.put(  'lastMeasurementTime:%d'%sensorID, ret, 24*3600 )
    return ret


def getSensorLastIntegral( sensorID ):
    global globalLastMeasurementTime
    global globalLastMeasurementValue
    global globalLastMeasurementEnergy 
    global globalLastMeasurementIntegral
    global globalLastMeasurementCacheTime
    now = long( time.time() )
    if (now - globalLastMeasurementCacheTime) > 15:
        globalLastMeasurementTime = {}
        globalLastMeasurementValue = {}
        globalLastMeasurementEnergy = {}
        globalLastMeasurementIntegral = {}
        globalLastMeasurementCacheTime = now

    if sensorID in globalLastMeasurementIntegral:
        return globalLastMeasurementIntegral[sensorID]

    logger.debug( 'lastMeasurementIntegral:%d'%sensorID )
    val = memcache.get( 'lastMeasurementIntegral:%d'%sensorID )
    if val != None:
        ret = float(val)
        globalLastMeasurementIntegral[sensorID] = ret
        return ret

    p = findMeasurementBefore( sensorID, now, "# DB search getSensorLastIntegral " )

    ret = 0.0
    if p is not None:
        if p.integral is not None:
            ret = p.integral

    memcache.put(  'lastMeasurementIntegral:%d'%sensorID, ret, 24*3600 )
    return ret


def getSensorLastEnergy( sensorID ):
    global globalLastMeasurementTime
    global globalLastMeasurementValue
    global globalLastMeasurementEnergy 
    global globalLastMeasurementIntegral
    global globalLastMeasurementCacheTime
    now = long( time.time() )
    if (now - globalLastMeasurementCacheTime) > 15:
        globalLastMeasurementTime = {}
        globalLastMeasurementValue = {}
        globalLastMeasurementEnergy = {}
        globalLastMeasurementIntegral = {}
        globalLastMeasurementCacheTime = now

    if sensorID in globalLastMeasurementEnergy:
       return globalLastMeasurementEnergy[sensorID]

    logger.debug( 'lastMeasurementEnergy:%d'%sensorID )
    val = memcache.get( 'lastMeasurementEnergy:%d'%sensorID )
    if val != None:
        ret = float(val)
        globalLastMeasurementEnergy[sensorID] = ret
        return ret

    p = findMeasurementBefore( sensorID, now, "# DB search getSensorLastEnergy " )
     
    ret = 0.0
    if p is not None:
        if p.energy is not None:
            ret = p.energy

    memcache.put(  'lastMeasurementEnergy:%d'%sensorID, ret, 24*3600 )
    return ret


def getSensorPower( sensorID , value=None):
    if value is None:
        value = getSensorValue( sensorID )

    if value is None:
       return 0.0

    sensorMeta = findSensorMetaByID( sensorID ) #  TODO move to cached form 
    watts = 0.0

    if ( sensorMeta['category'] == "Sensor") :
        if sensorMeta['units'] == "W":
            watts = value
    if sensorMeta['units'] == "%": #  TODO - can remove these 4 lines 
        if ( sensorMeta['watts'] != None ) :
            if sensorMeta['watts'] != 0.0:
                if ( value > 0.0 ):
                    watts = sensorMeta['watts']
    if sensorMeta['units'] == "%":
        if sensorMeta['unitsWhenOn'] == "W":
            if ( sensorMeta['valueWhenOn'] != None ) :
                if sensorMeta['valueWhenOn'] != 0.0:
                    if ( value > 0.0 ):
                        watts = sensorMeta['valueWhenOn']

    if sensorMeta['units'] == "C" or sensorMeta['units'] == "F":  #  TODO - can remove these 4 lines 
        if ( sensorMeta['watts'] != None ) and ( sensorMeta['threshold'] != None ):
            if value >= sensorMeta['threshold'] :
                watts = sensorMeta['watts']
    if sensorMeta['units'] == "C" or sensorMeta['units'] == "F":
        if sensorMeta['unitsWhenOn'] == "W":
            if ( sensorMeta['valueWhenOn'] != None ) and ( sensorMeta['threshold'] != None ):
                if value >= sensorMeta['threshold'] :
                    watts = sensorMeta['valueWhenOn']

    #assert watts >= 0.0 # todo - crash  galdstones sensor
    return watts
    



def storeMeasurementByName( sensorName, value, mTime=0, sum=None, reset=False ,energy=None, patchLevel=None ):
    sensorID = getSensorIDByName( sensorName )
    assert sensorID > 0
    storeMeasurement( sensorID, value, mTime=mTime, sum=sum, reset=reset, energy=energy,  patchLevel=patchLevel )


def storeMeasurement( sensorID, value, mTime=0, sum=None, reset=False , energy=None,  patchLevel=None  ):
    #userID = findUserID( userName )
    #if userName == "fluffy": #  TODO - this is a hack to auto create fluffy on any store 
    #    userID = findUserID( userName, True )
    #assert userID != 0, "Can not store measurement for user %s because that user does not exist"%userName

    # storeMeasurementOld( userName, sensorName, value )
    assert (value is not None) or ( sum is not None)

    # assert sum >= 0.0
    
    #sensorID = findSensorID(userName,sensorName,True)
    if value is None:
        v= float( 'nan' )
    else:
        v = float( value ) # TODO should catch excpetions
    
    sTime = 0
    if mTime <= 0:
        sTime = long( time.time() ) + mTime
    if mTime > 0:
        sTime = mTime
    sTime = long( sTime )
        
    logger.debug( "Store time in epoch seconds = %d"%sTime )

    integral = 0.0 
    newEnergy = 0.0

    #sensor = findSensor( sensorID ,"storeMeasurement" )
    #assert sensor is not None, "Problem finding sensor with ID %s "%sensorID

    # TODO - load from cache 
    p = None
    if sum is None:
        now = long( time.time() )
        p = findMeasurementBefore( sensorID, now, "# DB search for prev value for storeMeasurement" )
    
        if p is not None:
            if ( sTime >= p.time ):
                len = sTime - p.time
                val = p.value 
                
                if p.integral is None:
                    integral = 0.0
                else:
                    integral = p.integral

                integral += len*val

                if p.energy is None:
                    newEnergy = 0.0
                else:
                    newEnergy = p.energy

                watts = getSensorPower( sensorID , p.value )
                newEnergy = newEnergy + watts * len 

                #logger.debug( "Updating integral by len=%d val=%f watts=%f energy=%f"%(len,val,watts,newEnergy) )

    if sum is not None:
        integral = sum
        logger.debug( "Updating integral using provided sum %f"%sum )
        if getSensorUnitsByID(sensorID) == 'W':
            newEnergy = sum
            #logger.debug( "Updating energy using provided sum %f"%sum )

    if energy is not None:
        newEnergy = energy
        #logger.debug( "Updating energy using passed in energy value of %f"%energy )

    if (value is None) and (p is not None):
        if ( sTime > p.time ):
            len = sTime - p.time
            assert p.integral is not None
            assert len > 0 
            v = ( integral - p.integral ) / len
            logger.debug( "No value so reverse computed prev=%f curr=%f len=%f v=%f"%(p.integral, integral, len, v) )

    if patchLevel is None:
       patchLevel = 0
       
    m = Measurement2()
    m.sensorID = sensorID
    m.time = sTime
    m.value = v
    m.integral = integral
    m.energy = newEnergy
    m.patchLevel = patchLevel
    
    if reset:
        m.value = float('nan')
        m.integral = 0.0
        m.energy = 0.0

    patchMeasurement( m )
    saveMeasurement( m )
    logger.debug("# DB put for storeMeasurement id=%d value=%f integral=%d "%(m.sensorID,m.value,m.integral) )

    global globalLastMeasurementTime
    global globalLastMeasurementValue
    global globalLastMeasurementEnergy
    global globalLastMeasurementIntegral

    try:
        if sensorID in globalLastMeasurementTime:
            del globalLastMeasurementTime[sensorID]
        if sensorID in globalLastMeasurementValue:
            del globalLastMeasurementValue[sensorID]
        if sensorID in globalLastMeasurementEnergy:
            del globalLastMeasurementEnergy[sensorID]
        if sensorID in globalLastMeasurementIntegral:
            del globalLastMeasurementValue[sensorID]
    except KeyError:
        pass

    if mTime != 0 :
        logger.debug( "invalidating memcache values for sensor" )
        memcache.delete( 'lastMeasurementTime:%d'%sensorID )
        memcache.delete( 'lastMeasurementValue:%d'%sensorID )
        memcache.delete( 'lastMeasurementEnergy:%d'%sensorID )
        memcache.delete( 'lastMeasurementIntegral:%d'%sensorID )
    else:
        logger.debug( "update memcache values for sensor" )
        memcache.put(  'lastMeasurementEnergy:%d'%sensorID, m.energy, 24*3600 )
        memcache.put(  'lastMeasurementIntegral:%d'%sensorID, m.integral, 24*3600 )
        memcache.put(  'lastMeasurementTime:%d'%sensorID, m.time, 24*3600 )
        memcache.put(  'lastMeasurementValue:%d'%sensorID, m.value , 24*3600 )
     
    # update the hourly values 
    #hourTime = long(sTime)
    #hourTimr = hourTime - hourTime % 3600
    #if p is not None:
    #    if ( p.time <= hourTime ) and ( m.time >= hourTime ):
    #        computeHourlyBySensorID( sensorID, hourTime, p , m )




def getCurrentUsageOld(user):
    logger.debug("Getting current usage for user %s"%user )

    hydro = 0.0
    elec = findSensorPower( findSensorID( user, "All") , "Electricity" )
    gas =  findSensorPower( findSensorID( user, "All") , "Gas" )

    return { 'hydroUsage': hydro ,'elecUsage': elec, 'gasUsage': gas } 


    
def getDayValuesOld(userName,sensorName,time):
    time = datetime( time.year, time.month, time.day, time.hour ) - timedelta( hours=23 )
    
    vals = []
    for i in range(0,24):
        v = getHourlyDeltaSumHours(userName,sensorName,time)
        dict = { 'time': time, 'average': v } 
        vals.append( dict )
        time = time + timedelta( hours=1 )

    return vals



def getHourlyDeltaSumHoursOld(userName,streamName,ptime):
    startTime = datetime( ptime.year, ptime.month, ptime.day, ptime.hour )
    
    timeTuple = startTime.timetuple()
    floatTime =  time.mktime( timeTuple )
    utime = long( floatTime )

    #now = long( time.time() )
    #logger.debug( "TIME debug utime=%d now=%d diffMin/60=%d "%(utime,now,(now-utime)/60) )

    start = getSumSecondsInterplated( userName,streamName,utime)
    end   = getSumSecondsInterplated( userName,streamName,utime+60*60)

    diff = (end-start)/3600.0
    return diff


def getSensorIntegral(sensorID,utime,prev=None,next=None): # utime is unix integer time
    assert sensorID > 0

    logger.debug( 'integral:%d/%d'%(sensorID,utime) )
    val = memcache.get( 'integral:%d/%d'%(sensorID,utime) )
    if val != None:
        val = float( val )
        return val

    now = long( time.time() )
    assert utime <= now , "Can not interpolate sensor integrals in the future"
    
    logger.debug( "Looking for interpolated integral value at time %d"%utime )

    if prev is not None:
        if prev.time > utime :
            prev = None

    if next is not None:
        if next.time < utime :
            next = None

    # find before and after points
    if prev is None:
        prev = findMeasurementBefore( sensorID, utime, "# DB search for prev getSensorIntegral" )
        
    if next is None:
        next = findMeasurementAfter( sensorID, utime, "# DB search for next getSensorIntegral" )

    if prev != None and prev.integral == None:
        prev.integral = 0.0
    if next != None and next.integral == None:
        next.integral = 0.0 

    ret = 0.0

    # if neither exist, return 0.
    if ( prev is None ) and ( next is None ):
        logger.debug("interpolate, both were None")
        ret = 0.0
        # return ret # return here so this is not cached 

    # if no after, extrapolate based on current rate , can cache 
    if ( prev is not None ) and ( next is None ):
        ret = prev.integral
        v = prev.value
        len = utime - prev.time
        ret += v*len
        logger.debug("integral extrapolate for %d seconds",len)

    # if no before, just use zero. Can cache this 
    if ( prev is None) and ( next is not None ):
        ret =0.0
        logger.debug("no before")

    # if have before and after, interpolate between the two. can cache
    if ( prev is not None ) and ( next is not None ):
        if  prev.time == next.time :
            ret = (prev.integral+next.integral) / 2
        else:
            len = next.time - prev.time
            tim = utime - prev.time
            assert len > 0
            assert tim >= 0 , "tim=%d utime=%d prev.time=%d"%(tim,utime,prev.time)
            assert tim <= len
            delta = next.integral - prev.integral
            ret =  prev.integral + delta*tim/len
        logger.debug("interpolated sec before=%d sec after=%d "%( utime-prev.time , next.time-utime ) )
        logger.debug("interpolated bv=%f av=%f ret=%f "%( prev.integral , next.integral, ret ) )

    memcache.put( 'integral:%d/%d'%(sensorID,utime), ret , 24*3600 )
    return ret


def getSensorEnergy(sensorID, utime, prev=None, next=None ): # utime is unix integer time
    assert sensorID > 0

    logger.debug( 'getSensorEnergy:%d/%d'%(sensorID,utime) )
    val = memcache.get( 'getSensorEnergy:%d/%d'%(sensorID,utime) )
    if val != None:
        val = float( val )
        return val

    now = long( time.time() )
    assert utime <= now , "Can not interpolate sensor energy in the future"

    logger.debug( "Looking for interpolated Energy value at time %d"%utime )

    if prev is not None:
        if prev.time > utime :
            prev = None

    if next is not None:
        if next.time < utime :
            next = None

    # find before and after points
    if prev is None:
        prev = findMeasurementBefore( sensorID, utime, "# DB search for prev getSensorEnergy" )

    if next is None:
        next = findMeasurementAfter( sensorID, utime, "# DB search for next getSensorEnergy" )
        

    if prev != None and prev.energy == None:
        prev = None
    if next != None and next.energy == None:
        next = None 

    ret = 0.0

    # if neither exist, return 0.  can cache this 
    if ( prev is None ) and ( next is None ):
        logger.debug("interpolate, both were None")
        ret = 0.0
        #return ret

    # if no after, extrapolate based on current rate. can cache this 
    if ( prev is not None ) and ( next is None ):
        watts = getSensorPower( sensorID , prev.value )
        if watts != watts : # test for NaN
            assert prev.energy == prev.energy # check for NaN
            assert prev.energy >= 0
            ret = prev.energy 
            logger.debug("extrapolate for with no sensor reading from prev=%f ",prev.energy)
        else:
            len = utime - prev.time
            assert  len >= 0
            assert watts == watts # check for NaN
            assert watts >= 0.0
            assert prev.energy == prev.energy # check for NaN
            assert prev.energy >= 0
            ret = prev.energy + watts*len
            logger.debug("extrapolate for %d seconds, watts=%f prev=%f ",len, watts,prev.energy)

    # if no before, just use after zero. Can cache this 
    if ( prev is None) and ( next is not None ):
        ret = 0.0
        logger.debug("no before")

    # if have before and after, interpolate between the two. Cache in DB and memory 
    if ( prev is not None ) and ( next is not None ):
        if  prev.time == next.time :
            assert next.energy == next.energy # check for NaN
            assert prev.energy == prev.energy # check for NaN
            assert prev.energy >= 0.0
            assert next.energy >= 0.0
            ret = (prev.energy+next.energy) / 2
        else:
            len = next.time - prev.time
            tim = utime - prev.time
            assert len > 0
            assert tim >= 0
            assert tim <= len
            assert next.energy == next.energy # check for NaN
            assert prev.energy == prev.energy # check for NaN
            assert next.energy >= 0.0
            assert prev.energy >= 0.0
            delta = next.energy - prev.energy
            ret =  prev.energy + delta*tim/len
        logger.debug("interpolated sec before=%d sec after=%d "%( utime-prev.time , next.time-utime ) )
        logger.debug("interpolated bv=%f av=%f ret=%f "%( prev.energy , next.energy, ret ) )

    assert ret >= 0.0
    memcache.put( 'getSensorEnergy:%d/%d'%(sensorID,utime), ret , 24*3600 )
    return ret


################# OLD OLD OLD 



class EnrollInfo(models.Model): #  TODO remove indexes on some of these 
    sensorName = models.CharField(max_length=80) 
    user = models.CharField(max_length=80,blank=True)
    ipAddr = models.CharField(max_length=80)
    time = models.DateTimeField(auto_now_add=True)


def findEnroll( sensorName, ip ):
    query = EnrollInfo.objects
    logger.debug("# DB search for findEnroll" )
    query = query.filter( ipAddr = ip )
    query = query.filter( user = "" )
    query = query.filter( sensorName = sensorName )
    #  TODO - should time limit to 5 minutes 
    query = query.order_by("-time") 
    info = None
    try:
        info = query.all()[0]
    except IndexError:
        pass
    
    if info is None:
        info = EnrollInfo()
        info.sensorName = sensorName
        info.user =""
        info.ipAddr = ip
        info.save()
        logger.debug("# DB put for findEnroll" )
        logger.info("Got an enrollment request from new sensor %s at %s"%(sensorName,ip))
    else:
        logger.debug("Got an repeat enrollment request from  sensor %s at %s"%(sensorName,ip))

    return info


def findSensorsToEnroll( ip ):
    query = EnrollInfo.objects
    logger.debug("# DB search for findSensorsToEnroll ip=%s "%ip )
    query = query.filter( ipAddr = ip )
    query = query.filter( user = "" )
    #  TODO - should time limit to 5 minutes 
    query = query.order_by("-time") 
    results = query.all()

    ret = []
    for result in results:
        logger.debug("findSensorsToEnroll: found %s"%(  result.sensorName ) )
        ret.append( result.sensorName ) #  TODO - use a set and only insert once 

    return ret
    

    
def enrollSensor(ip,sensorName,user,secret):
    query = EnrollInfo.objects
    logger.debug("# DB search for enrollSensor" )
    query = query.filter( ipAddr = ip )
    query = query.filter( user = "" )
    query = query.filter( sensorName = sensorName )
    #  TODO - should time limit to 5 minutes 
    query = query.order_by("-time") 
    info = None
    try:
        info = query.all()[0]
    except IndexError:
        pass
    
    if info is None:
        return # weird error

    info.user = user
    info.save()
    logger.debug("# DB put for enrollSensor" )

    updateUserSettingsEpoch(user)

