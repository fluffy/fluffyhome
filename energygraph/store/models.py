# Copyright (c) 2010, Cullen Jennings. All rights reserved.

import logging
from datetime import timedelta
from datetime import datetime
import time
from sets import Set

# TODO switch to using memcache namespaces 

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.db import Key


class Sensor(db.Model):
    sensorID = db.IntegerProperty(required=True) # unique interger ID for this sensor 
    sensorName = db.StringProperty(required=True) # For a given user, this is a unique name used in URIs
    label = db.StringProperty(required=False,indexed=False) # human readable, changable, display name
    userID = db.IntegerProperty(required=True) # user that owns this sensor 
    apiKey = db.StringProperty(required=False,indexed=False) # TODO should we depricate this ?

    public = db.BooleanProperty(indexed=False) # data is public 
    hidden = db.BooleanProperty(indexed=False) # don't show the sensor on main displays of data 
    ignore = db.BooleanProperty(indexed=False) # don't include sensor in calculations  
    groupTotal = db.BooleanProperty(indexed=False) # don't show the sesnsor on main displays of data 
    killed = db.BooleanProperty(indexed=False) # mark this true to effetively delete a sensor

    category = db.StringProperty(indexed=True,required=False,choices=set(["Group", "Sensor"])) # dep , "Computed"
    type = db.StringProperty(indexed=False,required=False,choices=set([ "None","Electricity","Gas","Water"   ] )) # rename resource
                                                    #   , "Elecricity","Temp","Switch","Humidity", "Any" ])) #depricate lower ones
    units = db.StringProperty(indexed=False,choices=set(["None","V","W","C","F","lps","A","%","RH%","Pa"])) #,'k' 'Ws' #TODO fix, degC and degF
    unitsWhenOn = db.StringProperty(indexed=False,choices=set(["W","lps"])) 

    displayMin = db.FloatProperty(indexed=False) 
    displayMax = db.FloatProperty(indexed=False) 

    inGroup = db.IntegerProperty(required=False) # group this sensors is in

    watts = db.FloatProperty(indexed=False) # TODO depricate this and use valueWhenOn
    valueWhenOn = db.FloatProperty(indexed=False) 
    threshold = db.FloatProperty(indexed=False) 

    maxUpdateTime = db.IntegerProperty(indexed=False) # max time for update before sensor is considered "broken"


    
globalSensorMetaStore = {}
globalSensorMetaStoreEpoch = 0

def findSensorMetaByID(sensorID, callFrom=None):
    global globalSensorMetaStore
    global globalSensorMetaStoreEpoch

    epoch = getUserSettingEpochBySensorID( sensorID )
    assert epoch > 0 

    if globalSensorMetaStoreEpoch != epoch:
        globalSensorMetaStoreEpoch = epoch
        globalSensorMetaStore = {}

    if sensorID in globalSensorMetaStore:
        return globalSensorMetaStore[sensorID]

    #logging.debug( "In findSensorMetaByID sensorID=%s"%sensorID )
    assert  long( sensorID ) > 0 , "Problem with sensorID=%s"%sensorID

    logging.debug( 'key0-findSensorMetaByID:%d/%d'%(epoch,sensorID) ) 
    id = memcache.get( 'key0-findSensorMetaByID:%d/%d'%(epoch,sensorID) ) 
    if id != None:
        globalSensorMetaStore[sensorID] = id
        return id

    if callFrom is not None:
        logging.debug( "   calling findSensor from findSensorMetaByID from %s"%callFrom )
    else:
        logging.debug( "   calling findSensor from findSensorMetaByID" )

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
            'groupTotal' : sensor.groupTotal,
            'inGroup' : sensor.inGroup }

    globalSensorMetaStore[sensorID] = ret
    memcache.set( 'key0-findSensorMetaByID:%d/%d'%(epoch,sensorID), ret , 24*3600 )
    return ret


def getSensorUserIDByID(sensorID):
    assert sensorID > 0
    meta = findSensorMetaByID(sensorID,"getSensorUserIDByID")
    userID = meta['userID']
    assert userID > 0
    return userID


def getSensorCategoryByID(sensorID):
    assert sensorID > 0
    meta = findSensorMetaByID(sensorID,"getSensorCategoryByID")
    userID = meta['category']
    assert userID > 0
    return userID


def getSensorLabelByID(sensorID):
    assert sensorID > 0
    meta = findSensorMetaByID(sensorID,"getSensorLabelByID")
    label = meta['label']
    assert label is not None
    return label


def getSensorNamelByID(sensorID):
    assert sensorID > 0
    meta = findSensorMetaByID(sensorID,"getSensorNamelByID")
    name = meta['sensorName']
    assert name is not None
    return name


def getSensorUnitsByID(sensorID):
    assert sensorID > 0
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
                    assert v >= 0.0
                    sum += v
    return sum



def findGroupTotalSensorID( groupID , ignoreList ):
    """ 
    Find the sensorID of a sensor that meassures the groupTotal for this group. 
    returns 0 if none exist 
    """
    epoch = getUserSettingEpochBySensorID( groupID )
    logging.debug( 'key0-findGroupTotalSensorID:%d/%d'%(groupID,epoch) ) 
    id = memcache.get( 'key0-findGroupTotalSensorID:%d/%d'%(groupID,epoch) ) 
    if id != None:
        id = long(id)
        return id

    ret=0
    logging.debug( "Looking for group total sensor" )
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

    memcache.set( 'key0-findGroupTotalSensorID:%d/%d'%(groupID,epoch), ret , 24*3600 )
    return ret


def findSensorPower( sensorID , type="None" ,ignoreList=Set() ): #TODO - unify with getSensorPower 
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

    assert ret >= 0.0
    return ret


def findSensorWater( sensorID , type="None" , ignoreList=Set() ): #TODO - unify with getSensorPower 
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

    assert ret >= 0.0
    return ret



def findAllResourceSensors( userID , inGroupID=None ): #TODO  cache 
    assert userID > 0

    query = Sensor.all()
    logging.debug("# DB search for findAllResourceSensors" )
    query.filter( 'userID =' , userID )
    sensors = query.fetch(256)

    set = Set()
    if inGroupID is not None:
        assert inGroupID > 0 , "failed with inGroupID='%s'"%inGroupID
        set.add( inGroupID )
        done = False
        while not done:
            done = True
            for s in sensors: # if this sensor belongs to a group in the set, then add it and keep going 
                if s.sensorID not in set:
                    if s.inGroup in set:
                        set.add( s.sensorID )
                        done = False
    else:
        for s in sensors:
            set.add( s.sensorID )

    ret = []
    for sensor in sensors:
        if (sensor.killed != True) and (sensor.ignore != True) and ( sensor.sensorID in set ):
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
    query = Sensor.all()
    logging.debug("# DB search for findAllResourceSensors" )
    sensors = query.fetch(512)

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
    query = Sensor.all()
    logging.debug("# DB search for findAllSensorsInGroup calledby %s "%calledBy )

    query.filter( 'inGroup =' , groupID )
    sensors = query.fetch(100)

    ret = []
    for sensor in sensors:
        if sensor.killed != True:
            ret.append( sensor )

    return ret


def findAllSensorIDsInGroup( groupID , calledBy="" ):
    epoch = getUserSettingEpochBySensorID( groupID )

    logging.debug( 'key0-findAllSensorIDsInGroup:%d/%d'%(epoch,groupID) )
    id = memcache.get( 'key0-findAllSensorIDsInGroup:%d/%d'%(epoch,groupID) )
    if id != None:
        return id

    query = Sensor.all()
    logging.debug("# DB search for findAllSensorIDsInGroup calledby %s "%calledBy )
    query.filter( 'inGroup =' , groupID )
    sensors = query.fetch(100)

    ret = []
    for sensor in sensors:
        if sensor.killed != True:
            ret.append( sensor.sensorID )

    memcache.set( 'key0-findAllSensorIDsInGroup:%d/%d'%(epoch,groupID), ret, 24*3600 )

    logging.debug("findAllSensorIDsInGroup returned for group %s "%( groupID ) )

    return ret


def findAllSensorsByUserID( userID ):
    query = Sensor.all()
    logging.debug("# DB search for findAllSensorsByUserID" )
    query.filter( 'userID =' , userID )
    sensors = query.fetch(256)
    
    ret = []
    for sensor in sensors:
        if sensor.killed != True:
            ret.append( sensor )

    return ret


def findAllSensorsIDsByUserID( userID ):
    epoch = getUserSettingEpochByUserID( userID )

    logging.debug( 'key0-findAllSensorsIDsByUserID:%d/%d'%(epoch,userID) )
    id = memcache.get( 'key0-findAllSensorsIDsByUserID:%d/%d'%(epoch,userID) )
    if id != None:
        return id

    query = Sensor.all()
    logging.debug("# DB search for findAllSensorsIDsByUserID" )
    query.filter( 'userID =' , userID )
    sensors = query.fetch(256)

    ret = []
    for sensor in sensors:
        if sensor.killed != True:
            ret.append( sensor.sensorID )

    memcache.set( 'key0-findAllSensorsIDsByUserID:%d/%d'%(epoch,userID), ret, 24*3600 )
    return ret


def findAllGroupsIdNamePairs( userID ):
    ret = []
    query = Sensor.all()
    logging.debug("# DB search for findAllGroupsIdNamePairs" )
    query.filter( 'userID =' , userID )
    query.filter( 'category =' , "Group" )
    sensors = query.fetch(256)
    for sensor in sensors:
        if not sensor.killed:
            ret.append(  ( int(sensor.sensorID) , sensor.label ) )
    return ret



def findAllSensorIdNamePairs( userID ):
    ret = []
    query = Sensor.all()
    logging.debug("# DB search forfindAllSensorIdNamePairs " )
    query.filter( 'userID =' , userID )
    query.filter( 'category !=' , "Group" )
    sensors = query.fetch(256)
    for sensor in sensors:
        if not sensor.killed:
            ret.append(  ( sensor.sensorID , sensor.label ) )
    return ret


def findSensor( sensorID , calledBy="" ):
    query = Sensor.all()
    logging.debug("# DB search for findSensor called by %s "%calledBy )
    query.filter( 'sensorID =' , sensorID )
    sensor = query.get()
    return sensor


def sensorExistsByName( sensorName ):
    id = getSensorIDByName( sensorName )
    if id > 0:
        return True
    return False


def getSensorIDByName( sensorName ):
    logging.debug( 'key0-getSensorIDByName:%s'%(sensorName) )
    id = memcache.get( 'key0-getSensorIDByName:%s'%(sensorName) )
    if id != None:
        return id

    query = Sensor.all()
    logging.debug("# DB search for getSensorIDByName" )
    query.filter( 'sensorName =' , sensorName )
    sensor = query.get()
    
    ret = 0
    if sensor != None:
        ret = sensor.sensorID
        memcache.set( 'key0-getSensorIDByName:%s'%(sensorName) , ret, 24*3600 )
    else:
        memcache.set( 'key0-getSensorIDByName:%s'%(sensorName) , ret, 5 ) # keep bad sensor from hammering DB
    return ret 


def findSensorID( userName, sensorName, create=False , createGroup=False ):
    assert userName is not None, "Must pass valid userName" 
    assert sensorName is not None, "Must pass valid sensorName"

    logging.debug( 'key0-sensorID:%s/%s'%(userName,sensorName) )
    id = memcache.get( 'key0-sensorID:%s/%s'%(userName,sensorName) )
    if id != None:
        return long(id )

    userID = findUserIdByName( userName )
    if userID == 0:
        return 0

    query = Sensor.all()
    logging.debug("# DB search for findSensorID" )
    query.filter( 'userID =' , userID )
    query.filter( 'sensorName = ' , sensorName )
    sensor = query.get()

    if sensor is not None:
        # put in memcache 
        memcache.set(  'key0-sensorID:%s/%s'%(userName,sensorName), str(sensor.sensorID) , 3600 )
        return sensor.sensorID

    if not create:
        return 0

    sensorID = getNextSensorID()
    assert sensorID != 0

    # create a new sensor record 
    sensor = Sensor( sensorName=sensorName, userID=userID, sensorID=sensorID)

    sensor.userID = userID
    sensor.public = True
    sensor.killed = False
    sensor.hidden = False
    sensor.ignore = False
    sensor.label = sensorName

    if createGroup:
        sensor.category = "Group"
    else:
        sensor.category = "Sensor"
        
    if sensorName == "All":
        sensor.category = "Group"
        sensor.label = "All Group"
    else:
        sensor.inGroup = findSensorID(userName,"All",True)

    sensor.put()
    logging.debug("# DB create new sensor" )
    updateUserSettingsEpoch(userName)

    return sensorID


class AlarmData(db.Model):
    time  = db.IntegerProperty() # time this messarement was made (seconds since unix epoch)
    crit  = db.IntegerProperty() # 0=status, 1=info, 2=important, 3=alert 
    alarmID = db.IntegerProperty(required=False)
    eq = db.IntegerProperty(required=False,indexed=False)
    code = db.IntegerProperty(required=False) # todo should be true , and next one too 
    part = db.IntegerProperty(required=False)
    zone = db.IntegerProperty(required=False)
    user = db.IntegerProperty(required=False)
    note = db.StringProperty(required=False,indexed=False)


def addAlarmData( a, eq, c, p, crit, z=None, u=None, note=None ):
    rec = AlarmData()

    rec.time = long( time.time() )
    rec.alarmID = a
    rec.eq = eq
    rec.code = c
    rec.part = p
    rec.crit = crit
    rec.zone = z
    rec.user = u
    rec.note = note 

    logging.debug("saving alarm data account=%d user=%d eq=%d code=%d zone=%d part=%d"
                  %(rec.alarmID, rec.user, rec.eq, rec.code, rec.zone, rec.part) )

    rec.put()
    logging.debug("# DB put for addAlarmData" )


class SystemData(db.Model):
    nextSensorID = db.IntegerProperty()
    nextUserID = db.IntegerProperty()
    twitterConsumerToken  = db.StringProperty()
    twitterConsumerSecret = db.StringProperty()
    

def getSystemData():
    query = SystemData.all()
    logging.debug("# DB search for getSystemData" )
    sys = query.get()
    if sys is None:
        #create new sys data object 
        sys = SystemData()
        sys.nextSensorID =1
        sys.nextUserID = 1
        sys.twitterConsumerToken = ""
        sys.twitterConsumerSecret = ""
        sys.put()
        logging.debug("# DB create for getSystemData" )
    assert sys != None

    if sys.twitterConsumerToken == None:
        sys.twitterConsumerToken = ""
        sys.twitterConsumerSecret = ""
        sys.put()
        logging.debug("# DB update for getSystemData" )
        
    return sys


def getNextSensorID():
    sys = getSystemData()
    #TODO do as transaction
    id = sys.nextSensorID
    sys.nextSensorID = id +1 
    sys.put()
    logging.debug("# DB put for getNextSensorID" )
    return id


def getNextUserID():
    sys = getSystemData()
    #TODO do as transaction
    id = sys.nextUserID
    sys.nextUserID = id +1 
    sys.put()
    logging.debug("# DB put for getNextUserID" )
    return id


class User(db.Model):
    userName = db.StringProperty()
    email = db.StringProperty(indexed=False)
    twitter = db.StringProperty(indexed=False)
    purlKey = db.StringProperty(indexed=False)
    passwd = db.StringProperty(indexed=False)
    newPwd      = db.StringProperty(indexed=False)
    newPwdAgain = db.StringProperty(indexed=False)
    active = db.BooleanProperty(indexed=False)
    userID = db.IntegerProperty() 
    settingEpoch = db.IntegerProperty(indexed=False) # this increments each time the setting or sensors change for this user 
    timeZoneOffset = db.FloatProperty(indexed=False)
    midnightIs4Am = db.BooleanProperty(indexed=False)
    gasCost = db.FloatProperty(indexed=False)
    elecCost = db.FloatProperty(indexed=False)
    waterCost = db.FloatProperty(indexed=False)
    gasCO2 = db.FloatProperty(indexed=False)
    elecCO2 = db.FloatProperty(indexed=False)
    twitterAccessToken = db.StringProperty(indexed=False)
    twitterAccessSecret = db.StringProperty(indexed=False)
    twitterTempToken = db.StringProperty(indexed=True)
    twitterTempSecret = db.StringProperty(indexed=False)



def getUserPasswordHash( userName ):
    
    try:
        epoch = getUserSettingEpoch( userName )
    except AssertionError:
         logging.warning( "User %s does not exist"%userName )
         return None

    assert epoch > 0 
    logging.debug( 'key0-getUserPasswordHash:%d/%s'%(epoch,userName)  )
    id = memcache.get( 'key0-getUserPasswordHash:%d/%s'%(epoch,userName)  )
    if id != None:
        return id

    user = findUserByName( userName )
    if user is None:
        return None

    ret = user.passwd

    if user.passwd is None:
        user.passed = ""
        user.put()
        return ret
        
    if user.passwd is "": # don't allow empty passwords 
        return None

    memcache.set( 'key0-getUserPasswordHash:%d/%s'%(epoch,userName) ,ret , 24*3600 )
    return ret


def findAllUserNames( ):
    query = User.all()
    logging.debug("# DB search for findAllUserNames" )
    users = query.fetch(1024) # TODO uh, fix limit on number users 
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

    user.email = None
    user.twitter = None
    user.purlKey = None

    user.timeZoneOffset = -8.0
    user.midnightIs4Am = False
    user.gasCost = 0.0288
    user.elecCost = 0.06889
    user.waterCost = 0.001307
    user.gasCO2 = 0.19
    user.elecCO2 = 0.22

    user.settingEpoch = 1
    user.passwd = password # will not be able to log on till password is set

    twitterAccessToken = ""
    twitterAccessSecret = ""
    
    user.put()
    logging.debug("# DB put for createUser" )

    findSensorID( userName, "All", create=True )
    
    return id
    

def getUserMetaByUserID( userID ):
    epoch = getUserSettingEpochByUserID( userID )
    assert epoch > 0 

    logging.debug( 'key0-getUserMetaByUserID:%d/%d'%(epoch,userID) ) 
    id = memcache.get( 'key0-getUserMetaByUserID:%d/%d'%(epoch,userID) ) 
    if id != None:
        return id

    user = findUserByID( userID )
    assert user is not None

    ret = {
        "timeZoneOffset":user.timeZoneOffset,
        "gasCost":user.gasCost,
        "elecCost":user.elecCost,
        "waterCost":user.waterCost,
        "gasCO2":user.gasCO2,
        "elecCO2":user.elecCO2 }

    memcache.set( 'key0-getUserMetaByUserID:%d/%d'%(epoch,userID), ret , 24*3600 )
    return ret


def updateUserSettingsEpoch(userName):
    user = findUserByName( userName )
    assert user is not None
    #TODO do as transaction
    if user.settingEpoch is None:
        user.settingEpoch = 0
    user.settingEpoch =  user.settingEpoch + 1 
    user.put()
    logging.debug("# DB put for updateUserSettingsEpoch" )
    memcache.set( 'key0-UserSettingEpoch:%s'%(user.userName) , user.settingEpoch , 24*3600 )
    memcache.set( 'key0-getUserSettingEpochByUserID:%s'%(user.userID) , user.settingEpoch , 24*3600 )


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
            
    logging.debug( 'key0-UserSettingEpoch:%s'%(userName)  )
    id = memcache.get( 'key0-UserSettingEpoch:%s'%(userName)  )
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

    logging.debug("Doing cache set in getUserSettingEpoch userName=%s ret=%d"%(userName,ret) )
    memcache.set( 'key0-UserSettingEpoch:%s'%(userName) , ret , 24*3600 )
    return ret


def getUserSettingEpochByUserID(userID):
    logging.debug( 'key0-getUserSettingEpochByUserID:%s'%(userID)  )
    id = memcache.get( 'key0-getUserSettingEpochByUserID:%s'%(userID)  )
    if id != None:
        return long(id)

    user = findUserByID( userID )
    assert user is not None
    if user.settingEpoch is None:
        updateUserSettingsEpoch( user.userName )
        ret = 1
    else:
        ret = user.settingEpoch
    memcache.set( 'key0-getUserSettingEpochByUserID:%s'%(userID) , ret , 24*3600 )
    return ret



def getUserSettingEpochBySensorID(sensorID):
    return getUserSettingEpoch( findUserNameBySensorID( sensorID ))


globalUserNameBySensorID = {}

def findUserNameBySensorID(sensorID):
    global globalUserNameBySensorID

    if sensorID in globalUserNameBySensorID:
        return globalUserNameBySensorID[sensorID]

    logging.debug( 'key0-findUserNameBySensorID:%d'%(sensorID)  )
    id = memcache.get( 'key0-findUserNameBySensorID:%d'%(sensorID)  )
    if id != None:
        ret = id
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

    globalUserNameBySensorID[sensorID] = ret
    memcache.set( 'key0-findUserNameBySensorID:%d'%(sensorID) , ret , 24*3600 )
    return ret



def findUserIDByName( userName ): 
    logging.debug("Looking for user %s"%userName )
    # returns 0 if none found 

    id = None
    logging.debug( 'key0-userID:%s'%(userName) )
    id = memcache.get( 'key0-userID:%s'%(userName) )
    if id != None:
        return long(id)

    query = User.all()
    logging.debug("# DB search for findUserIDByName" )
    query.filter( 'userName =', userName )
    user = query.get()
    if user != None:
        id = user.userID
        logging.debug( "found user ID %d "%id )
        # put in memcache 
        memcache.set( 'key0-userID:%s'%(userName) , str(id) , 24*3600 )
        return id

    return 0
    

def findUserByName( userName ):
    query = User.all()
    logging.debug("# DB search for findUserByName" )
    query.filter( 'userName =', userName )
    user = query.get()
    return user


def findUserByID( userID ):
    query = User.all()
    logging.debug("# DB search for findUserByID" )
    query.filter( 'userID =', userID )
    user = query.get()
    assert user is not None
    return user


def findUserNameByID( userID ):
    logging.debug( 'key0-findUserNameByID:%d'%userID )
    val = memcache.get( 'key0-findUserNameByID:%d'%userID )
    if val != None:
        return val

    user = findUserByID( userID )
    assert user is not None
    ret = user.userName
    assert ret is not None

    memcache.set( 'key0-findUserNameByID:%d'%userID, ret, 24*3600 )
    return ret


def findUserIdByName( userName ):
    logging.debug( 'key0-findUserIdByName:%s'%userName )
    val = memcache.get( 'key0-findUserIdByName:%s'%userName )
    if val != None:
        return val

    user = findUserByName( userName )
    if user is None:
        return 0

    ret = user.userID
    assert ret is not None

    memcache.set( 'key0-findUserIdByName:%s'%userName, ret, 24*3600 )
    return ret



class Hourly2(db.Model):
    sensorID   = db.IntegerProperty() # system wide unique identifer for sensor 
    userID     = db.IntegerProperty() # user that owns the sensor
    time       = db.IntegerProperty() # time this messarement was made (seconds since unix epoch)
    integral   = db.FloatProperty() # integral of value over time up to this meassurment (units * seconds)
    value      = db.FloatProperty() # value of sensor at time of meassurment (units)
    joules     = db.FloatProperty() # cumulative energy used in watt seconds (Joules) #TODO rename energy
    hourOfDay  = db.IntegerProperty() # time this messarement was made (seconds since unix epoch)
    groupOtherValue = db.FloatProperty() # for groups, value of groupTotal - sum of group values (units)
    groupOtherEnergy = db.FloatProperty() # for groups, value of groupTotal - sum of group energy (units)


def hourlyUpgrade(): # does anything use this TODO 
    assert False
    query = Hourly2.all() 
    logging.debug("# DB search for hourlyUpgrade" )
    query.order("-time") 
    results = query.fetch( 1500) 

    i=0
    c=0
    for result in results:
        i = i+1
        if result.hourOfDay is None:
            result.hourOfDay =  (result.time / 3600) % 24 
            result.put()
            c = c + 1
            logging.debug("Updated result # %d"%i )
            if c > 200 :
                return False

    logging.debug("Done with hourlyUpgrade of %d items"%i )   
    return True


def getHourlyByUserIDTime( userID, start=None, end=None , hour=None ):
    utime = long(  time.time() )
    utime = utime - utime % 3600

    if start is None:
        start = utime - 24*3600
    if end is None:
        end = utime

    if end > utime:
        end = utime

    query = Hourly2.all() 
    logging.debug("# DB search for getHourlyByUserIDTime" )
    query.filter( 'userID =', userID )
    if hour is not None:
        query.filter( 'hourOfDay =', hour )
    query.filter("time <= ", end) 
    query.filter("time >= ", start ) 
    query.order("-time") 
    results = query.fetch(5000) 

    return results


def getHourlyEnergyTotalByGroupID( groupID, utime ):
    assert groupID > 0
    assert utime > 0 
    
    logging.debug( 'key0-getHourlyEnergyTotalByGroupID:%d/%d'%(groupID,utime) )
    val = memcache.get( 'key0-getHourlyEnergyTotalByGroupID:%d/%d'%(groupID,utime) )
    if val != None:
        return val

    gt = findGroupTotalSensorID( groupID , Set() )
    if gt != 0:
        ret = getHourlyEnergyBySensorID( gt, utime )
    else:
        sum = 0.0
        sensors = findAllSensorsInGroup( groupID ,"getHourlyEnergyTotalByGroupID" ) #TODO fix form to cache 
        for sensor in sensors:
            if ( sensor.ignore != True ) and ( sensor.killed != True ) and (sensor.groupTotal != True ):
                if sensor.category == "Sensor" :
                    v = getHourlyEnergyBySensorID( sensor.sensorID , utime )
                    assert v >= 0.0 
                    sum += v
                if sensor.category == "Group" :
                    v = getHourlyEnergyTotalByGroupID( sensor.sensorID , utime )
                    assert v >= 0.0 
                    sum += v
        ret = sum

    assert ret >= 0.0
    memcache.set(  'key0-getHourlyEnergyTotalByGroupID:%d/%d'%(groupID,utime), ret, 5*60 )
    return ret


def getHourlyEnergyOtherByGroupID( groupID, utime ):
    assert groupID > 0
    assert utime > 0 
    
    logging.debug( 'key0-getHourlyEnergyOtherByGroupID:%d/%d'%(groupID,utime) )
    val = memcache.get( 'key0-getHourlyEnergyOtherByGroupID:%d/%d'%(groupID,utime) )
    if val != None:
        return val

    #logging.debug( "Start getHourlyEnergyOtherByGroupID for group %s"%(getSensorLabelByID( groupID ) ) )

    gt = findGroupTotalSensorID( groupID , Set() )
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
                #logging.debug("sum sensor in label=%s sum=%f"%( getSensorLabelByID(sensor.sensorID),sum))
                if v >= 0.0 :
                    sum += v
            if sensor.category == "Group" :
                v = getHourlyEnergyTotalByGroupID( sensor.sensorID , utime )
                #logging.debug("sum group in label=%s sum=%f"%( getSensorLabelByID(sensor.sensorID),sum))
                if v >= 0.0 :
                    sum += v

    assert total >= 0.0
    assert sum >= 0.0
    ret = total - sum 
    #logging.debug("End getHourlyEnergyOtherByGroupID groupid=%d label=%s sum=%f total=%f ret=%f"%(groupID,
    #                                                                                             getSensorLabelByID(groupID),
    #                                                                                             sum,total,ret))

    if ret < 0.0:
        ret = 0.0 

    assert ret >= 0.0
    memcache.set(  'key0-getHourlyEnergyOtherByGroupID:%d/%d'%(groupID,utime), ret, 5*60 )
    return ret


def getHourlyEnergyBySensorID( sensorID, utime ): # TODO - can we get rid of this 
    assert sensorID > 0
    assert utime > 0 ,  "Problem with invalid utime of %d"%utime
    assert utime <= long( time.time() )

    utime = long( utime )
    utime = utime - utime % 3600

    logging.debug( 'key0-getHourlyEnergyBySensorID:%d/%d'%(sensorID,utime) )
    val = memcache.get( 'key0-getHourlyEnergyBySensorID:%d/%d'%(sensorID,utime) )
    if val != None:
        return val

    logging.debug("getHourlyEnergyBySensorID: sensorID=%d time=%d hour ago"%( sensorID ,
                                                                              (utime-time.time())/3600.0 ) )

    query = Hourly2.all() 
    logging.debug("# DB search for getHourlyEnergyBySensorID" )
    query.filter( 'sensorID =', sensorID )
    query.filter("time", utime) 
    hourly = query.get()

    if hourly is None:
        hourly = computeHourlyBySensorID( sensorID , utime )
        
    assert hourly is not None

    assert hourly.joules >= 0.0
    memcache.set(  'key0-getHourlyEnergyBySensorID:%d/%d'%(sensorID,utime), hourly.joules, 24*3600 )
    return hourly.joules



def getHourlyIntegralBySensorID( sensorID, utime ):
    assert sensorID > 0
    assert utime > 0, "Problem with invalid utime of %d"%utime
    assert utime <= long( time.time() )

    logging.debug( 'key0-getHourlyIntegralBySensorID:%d/%d'%(sensorID,utime) )
    val = memcache.get( 'key0-getHourlyIntegralBySensorID:%d/%d'%(sensorID,utime) )
    if val != None:
        return val

    utime = long( utime )
    utime = utime - utime % 3600

    query = Hourly2.all() 
    logging.debug("# DB search for getHourlyIntegralBySensorID" )
    query.filter( 'sensorID =', sensorID )
    query.filter("time", utime) 
    hourly = query.get()

    if hourly is None:
        hourly = computeHourlyBySensorID( sensorID , utime )

    assert hourly is not None

    memcache.set(  'key0-getHourlyIntegralBySensorID:%d/%d'%(sensorID,utime), hourly.integral, 24*3600 )
    return hourly.integral
  


def computeHourlyBySensorID( sensorID, utime, prev=None, next=None ):
    logging.debug( "In computeHourlyBySensorID sensorid=%d "%(sensorID) )
    assert sensorID > 0
    assert utime > 0
    assert utime <= long( time.time() )

    utime = long( utime )
    utime = utime - utime % 3600

    # find before and after points
    if prev is None:
        query = Measurement2.all() 
        logging.debug("# DB search for prev getSensorIntegral" )
        query.filter( 'sensorID =', sensorID )
        query.filter( 'time <=', utime )
        query.order("-time") 
        prev = query.get() 
        
    if next is None:
        query = Measurement2.all() 
        logging.debug("# DB search for next getSensorIntegral " )
        query.filter( 'sensorID =', sensorID )
        query.filter( 'time >=', utime )
        query.order("time") 
        next = query.get() 

    query = Hourly2.all() 
    logging.debug("# DB search for computeHourlyBySensorID" )
    query.filter( 'sensorID =', sensorID )
    query.filter("time", utime) 
    hourly = query.get()

    if hourly is None:
        hourly = Hourly2()
        hourly.sensorID = sensorID
        hourly.time = utime 
        hourly.hourOfDay = (hourly.time / 3600) % 24 
        meta = findSensorMetaByID( sensorID )
        assert meta is not None
        hourly.userID = meta['userID'] 
        assert hourly.userID > 0 
  
    hourly.integral = 0.0
    hourly.value = 0.0
    hourly.joules = 0.0
    hourly.groupOtherValue = 0.0
    hourly.groupOtherEnergy = 0.0

    if prev is not None:
        hourly.integral = getSensorIntegral(sensorID,utime,prev,next)
        hourly.value = prev.value
        hourly.joules = getSensorEnergy(sensorID,utime,prev,next)

    if getSensorCategoryByID( sensorID ) == "Group":
        hourly.joules = getHourlyEnergyTotalByGroupID(sensorID,utime)
        hourly.groupOtherValue = 0.0 # TODO 
        hourly.value = 0.0 # TODO
        hourly.integral = 0.0 #  TODO ? not clear what this would be 
        hourly.groupOtherEnergy = getHourlyEnergyOtherByGroupID( sensorID, utime )

    logging.debug("# DB put for computeHourlyBySensorID" )
    hourly.put()

    logging.debug( "hourly integral = %f"%hourly.integral )
    logging.debug( "hourly value = %f"%hourly.value )
    logging.debug( "hourly joules = %f"%hourly.joules )

    return hourly



class KnownIP(db.Model):
    ip       = db.StringProperty(required=True)
    time     = db.IntegerProperty(required=False) # time this messarement was made (seconds since unix epoch)
    sensorID = db.IntegerProperty(required=False) # system wide unique identifer for sensor


def addKnownIP( ip, sensorName=None ):
    sensorID = 0
    if sensorName !=None:
        sensorID = getSensorIDByName( sensorName )
        
    if checkKnownIP( ip, sensorID, calledBy="addKnownIP"):
        return

    knownIP = KnownIP( ip=ip, sensorID=sensorID , time=long( time.time() ) )
    knownIP.put()
    logging.debug("# DB create new KnownIP for ip=%s sensor=%s"%(ip,sensorName) )
   
    return


def checkKnownIP( ip, sensorID=0, calledBy=""):
    cachekey = "key0-checkKnownIPfoo:%s/%d"%(ip,sensorID)
    logging.debug( cachekey) 
    id = memcache.get( cachekey ) 
    if id != None:
        return True
 
    query = KnownIP.all()
    logging.debug("# DB search for KnownIP=%s sensorID=%d calledby=%s "%(ip,sensorID,calledBy) )
    query.filter( 'ip =' , ip )
    query.filter( 'sensorID =' , sensorID )
    query.order("-time") 
    knownIP = query.get()

    if knownIP == None:
        return False

    memcache.set( cachekey, True , 24*3600 ) 
    return True


def findAllKnownIP():
    query = KnownIP.all()
    logging.debug("# DB search for findAllKnownIP" )
    query.filter( 'sensorID =' , 0 )
    query.order("-time") 
    ips = query.fetch(1024)

    ret = Set()
    for ip in ips:
        ret.add( ip.ip )
    return ret


def findIPforSensorID( sensorID ):
    query = KnownIP.all()
    logging.debug("# DB search for findAllKnownIP" )
    query.filter( 'sensorID =' , sensorID )
    query.order("-time") 
    ips = query.fetch(1024)

    ret = None
    for ip in ips:
        ret = ip.ip 
    return ret
   
    
class Measurement2(db.Model):
    sensorID   = db.IntegerProperty() # system wide unique identifer for sensor
    time       = db.IntegerProperty() # time this messarement was made (seconds since unix epoch)
    integral   = db.FloatProperty() # integral of value over time up to this meassurment (units * seconds)
    value      = db.FloatProperty() # value of sensor at time of meassurment (units)
    joules     = db.FloatProperty() # cumulative energy used in watt seconds (Joules) # TODO rename energy



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

    now = long(  time.time() )
    now = now - now%15 # round to lower 15 seconds 
    
    if globalLastMeasurementCacheTime != now:
        globalLastMeasurementTime = {}
        globalLastMeasurementValue = {}
        globalLastMeasurementEnergy = {}
        globalLastMeasurementIntegral = {}
        globalLastMeasurementCacheTime = now

    if sensorID in globalLastMeasurementValue:
        return globalLastMeasurementValue[sensorID]

    logging.debug( 'key0-lastMeasurementValue:%d'%sensorID )
    val = memcache.get( 'key0-lastMeasurementValue:%d'%sensorID )
    if val != None:
        ret = float(val)
        globalLastMeasurementValue[sensorID] = ret
        return ret

    query = Measurement2.all() 
    logging.debug("# DB search for getSensorValue for sensor %s"%( getSensorNamelByID(sensorID) ))
    query.filter( 'sensorID =', sensorID )
    query.order("-time") 
    p = query.get() 
    
    ret = 0.0
    if p is not None:
        ret = float( p.value )

    memcache.set(  'key0-lastMeasurementValue:%d'%sensorID, ret , 24*3600 )
    return ret


def getSensorLastTime( sensorID ):

    if sensorID in globalLastMeasurementTime:
        return globalLastMeasurementTime[sensorID]

    logging.debug( 'key0-lastMeasurementTime:%d'%sensorID )
    val = memcache.get( 'key0-lastMeasurementTime:%d'%sensorID )
    if val != None:
        ret = float(val)
        globalLastMeasurementTime[sensorID] = ret
        return ret

    query = Measurement2.all() 
    logging.debug("# DB search getSensorLastTime " )
    query.filter( 'sensorID =', sensorID )
    query.order("-time") 
    p = query.get() 

    ret = 0
    if p is not None:
        ret = long( p.time )

    memcache.set(  'key0-lastMeasurementTime:%d'%sensorID, ret, 24*3600 )
    return ret


def getSensorLastIntegral( sensorID ):

    if sensorID in globalLastMeasurementIntegral:
        return globalLastMeasurementIntegral[sensorID]

    logging.debug( 'key0-lastMeasurementIntegral:%d'%sensorID )
    val = memcache.get( 'key0-lastMeasurementIntegral:%d'%sensorID )
    if val != None:
        ret = float(val)
        globalLastMeasurementIntegral[sensorID] = ret
        return ret

    query = Measurement2.all() 
    logging.debug("# DB search for getSensorLastIntegral" )
    query.filter( 'sensorID =', sensorID )
    query.order("-time") 
    p = query.get() 

    ret = 0.0
    if p is not None:
        if p.integral is not None:
            ret = p.integral

    memcache.set(  'key0-lastMeasurementIntegral:%d'%sensorID, ret, 24*3600 )
    return ret


def getSensorLastEnergy( sensorID ):
    if sensorID in globalLastMeasurementEnergy:
       return globalLastMeasurementEnergy[sensorID]

    logging.debug( 'key0-lastMeasurementEnergy:%d'%sensorID )
    val = memcache.get( 'key0-lastMeasurementEnergy:%d'%sensorID )
    if val != None:
        ret = float(val)
        globalLastMeasurementEnergy[sensorID] = ret
        return ret

    query = Measurement2.all() 
    logging.debug("# DB search for getSensorLastEnergy" )
    query.filter( 'sensorID =', sensorID )
    query.order("-time") 
    p = query.get() 

    ret = 0.0
    if p is not None:
        if p.joules is not None:
            ret = p.joules

    memcache.set(  'key0-lastMeasurementEnergy:%d'%sensorID, ret, 24*3600 )
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

    assert watts >= 0.0
    return watts
    

def findRecentMeasurements( sensorID ):
    now = long( time.time() )
    t = now
    t = t - 36*60*60

    query = Measurement2.all() 
    logging.debug("# DB search for findRecentMeasurements" )
    query.filter( 'sensorID =', sensorID )
    query.filter( 'time >', t )
    query.order("-time") 
    p = query.fetch(32) 
    return p


def storeMeasurementByName( sensorName, value, mTime=0, sum=None, reset=False ,joules=None ):
    sensorID = getSensorIDByName( sensorName )
    assert sensorID > 0
    storeMeasurement( sensorID, value, mTime=mTime, sum=sum, reset=reset, joules=joules )


def storeMeasurement( sensorID, value, mTime=0, sum=None, reset=False , joules=None  ):
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
        
    logging.debug( "Store time in epoch seconds = %d"%sTime )

    integral = 0.0 
    newJoules = 0.0

    #sensor = findSensor( sensorID ,"storeMeasurement" )
    #assert sensor is not None, "Problem finding sensor with ID %s "%sensorID

    # TODO - load from cache 
    p = None
    if sum is None:
        query = Measurement2.all() 
        logging.debug("# DB search for prev value for storeMeasurement" )
        query.filter( 'sensorID =', sensorID )
        query.order("-time") 
        p = query.get() 
        if p is not None:
            if ( sTime >= p.time ):
                len = sTime - p.time
                val = p.value 
                
                if p.integral is None:
                    integral = 0.0
                else:
                    integral = p.integral

                integral += len*val

                if p.joules is None:
                    newJoules = 0.0
                else:
                    newJoules = p.joules

                watts = getSensorPower( sensorID , p.value )
                newJoules = newJoules + watts * len 

                logging.debug( "Updating integral by len=%d val=%f watts=%f joules=%f"%(len,val,watts,newJoules) )

    if sum is not None:
        integral = sum
        logging.debug( "Updating integral using provided sum %f"%sum )
        if getSensorUnitsByID(sensorID) == 'W':
            newJoules = sum
            logging.debug( "Updating joules using provided sum %f"%sum )

    if joules is not None:
        newJoules = joules
        logging.debug( "Updating joules using passed in joules value of %f"%joules )

    if (value is None) and (p is not None):
        if ( sTime > p.time ):
            len = sTime - p.time
            assert p.integral is not None
            assert len > 0 
            v = ( integral - p.integral ) / len
            logging.debug( "No value so reverse computed prev=%f curr=%f len=%f v=%f"%(p.integral, integral, len, v) )

    m = Measurement2()
    m.sensorID = sensorID
    m.time = sTime
    m.value = v
    m.integral = integral
    m.joules = newJoules

    if reset:
        m.value = float('nan')
        m.integral = 0.0
        m.joules = 0.0

    m.put()
    logging.debug("# DB put for storeMeasurement" )

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

    #logging.debug( "About to update memcach values" )
  
    if mTime != 0 :
        #invalidate RecentMeasurement Cache
        memcache.delete( 'key0-lastMeasurementTime:%d'%sensorID )
        memcache.delete( 'key0-lastMeasurementValue:%d'%sensorID )
        memcache.delete( 'key0-lastMeasurementEnergy:%d'%sensorID )
        memcache.delete( 'key0-lastMeasurementIntegral:%d'%sensorID )
    else:
        memcache.set(  'key0-lastMeasurementEnergy:%d'%sensorID, m.joules, 24*3600 )
        memcache.set(  'key0-lastMeasurementIntegral:%d'%sensorID, m.integral, 24*3600 )
        memcache.set(  'key0-lastMeasurementTime:%d'%sensorID, m.time, 24*3600 )
        memcache.set(  'key0-lastMeasurementValue:%d'%sensorID, m.value , 24*3600 )

    #logging.debug( "Done update memcach values" )
     
    # update the hourly values 
    #hourTime = long(sTime)
    #hourTimr = hourTime - hourTime % 3600
    #if p is not None:
    #    if ( p.time <= hourTime ) and ( m.time >= hourTime ):
    #        computeHourlyBySensorID( sensorID, hourTime, p , m )




def getCurrentUsageOld(user):
    logging.info("Getting current usage for user %s"%user )

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
    #logging.debug( "TIME debug utime=%d now=%d diffMin/60=%d "%(utime,now,(now-utime)/60) )

    start = getSumSecondsInterplated( userName,streamName,utime)
    end   = getSumSecondsInterplated( userName,streamName,utime+60*60)

    diff = (end-start)/3600.0
    return diff


def getSensorIntegral(sensorID,utime,prev=None,next=None): # utime is unix integer time
    assert sensorID > 0

    logging.debug( 'key0-integral:%d/%d'%(sensorID,utime) )
    val = memcache.get( 'key0-integral:%d/%d'%(sensorID,utime) )
    if val != None:
        return val

    now = long( time.time() )
    assert utime <= now , "Can not interpolate sensor integrals in the future"
    
    logging.debug( "Looking for interpolated integral value at time %d"%utime )

    if prev is not None:
        if prev.time > utime :
            prev = None

    if next is not None:
        if next.time < utime :
            next = None

    # find before and after points
    if prev is None:
        query = Measurement2.all() 
        logging.debug("# DB search for prev getSensorIntegral" )
        query.filter( 'sensorID =', sensorID )
        query.filter( 'time <=', utime )
        query.order("-time") 
        prev = query.get() 
        
    if next is None:
        query = Measurement2.all() 
        logging.debug("# DB search for next getSensorIntegral " )
        query.filter( 'sensorID =', sensorID )
        query.filter( 'time >=', utime )
        query.order("time") 
        next = query.get() 

    if prev != None and prev.integral == None:
        prev.integral = 0.0
    if next != None and next.integral == None:
        next.integral = 0.0 

    ret = 0.0

    # if neither exist, return 0.
    if ( prev is None ) and ( next is None ):
        logging.debug("interpolate, both were None")
        ret = 0.0
        # return ret # return here so this is not cached 

    # if no after, extrapolate based on current rate , can cache 
    if ( prev is not None ) and ( next is None ):
        ret = prev.integral
        v = prev.value
        len = utime - prev.time
        ret += v*len
        logging.debug("integral extrapolate for %d seconds",len)

    # if no before, just use zero. Can cache this 
    if ( prev is None) and ( next is not None ):
        ret =0.0
        logging.debug("no before")

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
        logging.debug("interpolated sec before=%d sec after=%d "%( utime-prev.time , next.time-utime ) )
        logging.debug("interpolated bv=%f av=%f ret=%f "%( prev.integral , next.integral, ret ) )

    memcache.set( 'key0-integral:%d/%d'%(sensorID,utime), ret , 24*3600 )
    return ret


def getSensorEnergy(sensorID, utime, prev=None, next=None ): # utime is unix integer time
    assert sensorID > 0

    logging.debug( 'key0-getSensorEnergy:%d/%d'%(sensorID,utime) )
    val = memcache.get( 'key0-getSensorEnergy:%d/%d'%(sensorID,utime) )
    if val != None:
        return val

    now = long( time.time() )
    assert utime <= now , "Can not interpolate sensor energy in the future"

    logging.debug( "Looking for interpolated Energy value at time %d"%utime )

    if prev is not None:
        if prev.time > utime :
            prev = None

    if next is not None:
        if next.time < utime :
            next = None

    # find before and after points
    if prev is None:
        query = Measurement2.all() 
        logging.debug("# DB search for prev getSensorEnergy" )
        query.filter( 'sensorID =', sensorID )
        query.filter( 'time <=', utime )
        query.order("-time") 
        prev = query.get() 

    if next is None:
        query = Measurement2.all() 
        logging.debug("# DB search for next getSensorEnergy" )
        query.filter( 'sensorID =', sensorID )
        query.filter( 'time >=', utime )
        query.order("time") 
        next = query.get() 

    if prev != None and prev.joules == None:
        prev = None
    if next != None and next.joules == None:
        next = None 

    ret = 0.0

    # if neither exist, return 0.  can cache this 
    if ( prev is None ) and ( next is None ):
        logging.debug("interpolate, both were None")
        ret = 0.0
        #return ret

    # if no after, extrapolate based on current rate. can cache this 
    if ( prev is not None ) and ( next is None ):
        watts = getSensorPower( sensorID , prev.value )
        logging.debug("*** value=%d watts=%d "%(prev.value,watts) )
        len = utime - prev.time
        assert  len >= 0
        ret = prev.joules + watts*len
        logging.debug("extrapolate for %d seconds, watts=%f prev=%f ",len, watts,prev.joules)
        #return ret

    # if no before, just use after zero. Can cache this 
    if ( prev is None) and ( next is not None ):
        ret = 0.0
        logging.debug("no before")

    # if have before and after, interpolate between the two. Cache in DB and memory 
    if ( prev is not None ) and ( next is not None ):
        if  prev.time == next.time :
            ret = (prev.joules+next.joules) / 2
        else:
            len = next.time - prev.time
            tim = utime - prev.time
            assert len > 0
            assert tim >= 0
            assert tim <= len
            delta = next.joules - prev.joules
            ret =  prev.joules + delta*tim/len
        logging.debug("interpolated sec before=%d sec after=%d "%( utime-prev.time , next.time-utime ) )
        logging.debug("interpolated bv=%f av=%f ret=%f "%( prev.joules , next.joules, ret ) )

    assert ret >= 0.0
    memcache.set( 'key0-getSensorEnergy:%d/%d'%(sensorID,utime), ret , 24*3600 )
    return ret


################# OLD OLD OLD 



class EnrollInfo(db.Model): #  TODO remove indexes on some of these 
    sensorName = db.StringProperty() 
    user = db.StringProperty()
    ipAddr = db.StringProperty()
    secret = db.StringProperty()
    time = db.DateTimeProperty(auto_now_add=True)


def findEnroll( sensorName, ip ):
    query = EnrollInfo.all()
    logging.debug("# DB search for findEnroll" )
    query.filter( 'ipAddr =', ip )
    query.filter( 'user =', "" )
    query.filter( 'sensorName =', sensorName )
    #  TODO - should time limit to 5 minutes 
    query.order("-time") 
    info = query.get()

    if info is None:
        info = EnrollInfo()
        info.sensorName = sensorName
        info.user =""
        info.ipAddr = ip
        info.put()
        logging.debug("# DB put for findEnroll" )
        logging.info("Got an enrollment request from new sensor %s at %s"%(sensorName,ip))
    else:
        logging.debug("Got an repeat enrollment request from  sensor %s at %s"%(sensorName,ip))

    return info


def findSensorsToEnroll( ip ):
    query = EnrollInfo.all()
    logging.debug("# DB search for findSensorsToEnroll" )
    query.filter( 'ipAddr =', ip )
    query.filter( 'user =', "" )
    #  TODO - should time limit to 5 minutes 
    query.order("-time") 
    results = query.fetch(100)

    ret = []
    for result in results:
        ret.append( result.sensorName ) #  TODO - use a set and only insert once 

    return ret
    

    
def enrollSensor(ip,sensorName,user,secret):
    query = EnrollInfo.all()
    logging.debug("# DB search for enrollSensor" )
    query.filter( 'ipAddr =', ip )
    query.filter( 'user =', "" )
    query.filter( 'sensorName =', sensorName )
    #  TODO - should time limit to 5 minutes 
    query.order("-time") 
    info = query.get()

    if info is None:
        return # weird error

    info.user = user
    info.secret = secret 
    info.put()
    logging.debug("# DB put for enrollSensor" )

    updateUserSettingsEpoch(user)

