# Copyright (c) 2010, Cullen Jennings. All rights reserved.

import logging
import sys
import os
import copy
import time
import re
import string

from datetime import timedelta
from datetime import datetime
from datetime import tzinfo

from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.http import HttpResponseGone
from django.shortcuts import render_to_response

from django import forms

from django import VERSION as DJANGO_VERSION
#from django.utils import simplejson as json  # fix when we can use Python 2.6 to just be import json 
import json

from django.contrib.auth.decorators import login_required


#from djangohttpdigest.decorators import digestProtect,digestLogin

from energygraph.store.models import *

from energygraph.store.cache import *



logger = logging.getLogger('energygraph')

    
    
def editUser( request, userName ):
    record = findUserByName( userName )
    
    if record is not None:
        return HttpResponse("<h1>User %s already exists</h1>"%(userName) )

    password = "123456" # TODO fix to use random 
    createUser( userName , password  ) 
    return HttpResponse("<h1>Created user: %s with password %s </h1>"%(userName,password) )
 

class EditUserForm( forms.ModelForm):
    class Meta:
        model = User
        exclude = [ 'userName','passwd','active','userID','settingEpoch','newPwd','newPwdAgain' ]
    def __init__(self, *args, **kwargs):
        super( forms.ModelForm, self).__init__(*args, **kwargs)



#@digestProtect(realm='fluffyhome.com') # TODO get from settings file 
@login_required()
def userPrefs( request, userName ):
    msg = "Edit any values you wish to change above then press Update"

    record = findUserByName( userName )
    assert record is not None, "can't find record in DB"

    if request.method == 'POST': 
        form = EditUserForm(request.POST, instance=record)
        if form.is_valid():
            logger.debug( "input form IS valid" )

            #logger.debug( "form extra group = %s", form.cleaned_data['extraGroup'] )

            info = form.save(commit=False)
        
            #logger.debug( "form extra group = %s", info.extraGroup )
            logger.debug( "done" )
            
            msg ="Data succesfully saved"

            #if ( record.newPwd is not None ) and ( record.newPwd is not "" ) :
            #    if record.newPwd == record.newPwdAgain :
            #        record.passwd = record.newPwd
            #        msg ="Password succesfully changed"
            #        record.newPwd = ""
            #        record.newPwdAgain = ""
            #    else:
            #        msg ="New passwords did not match and password was not changed"

            record.save()
            updateUserSettingsEpoch(userName)
        else:
            logger.error( "Errr in form data to edit sensor form=%s"%( str( form )) )
            msg = "Some problem processing form"
            
    else:
        form = EditUserForm( instance=record ,  auto_id=False  )

    twitterEnabled = False
    if record.twitterAccessToken:
        if record.twitterAccessToken != '':
            twitterEnabled = True
        
    logger.debug( "debug for form=%s"%form )
    return render_to_response('userPrefs.html', { 'msg':msg, 
                                                  'form':form,
                                                  'user':userName,
                                                  'twitterEnabled':twitterEnabled,
                                                  'host' : request.META["HTTP_HOST"] } )



#@digestProtect(realm='fluffyhome.com') # TODO get from settings file 
@login_required()
def showStats( request ):
    template = "showStats.html"
    
    now = long( time.time() )
    day = now - now % (24*3600)
    now = long( time.time() )
    minute0 = now - now % 60
    now = now-60;
    minute1 = now - now % 60

    sensors = findAllNonGroupSensors( )
    for s in sensors:
        cacheKey = "key4-sensorTokenBucketDay%s/%s"%( s['name'], day )
        updates = memcache.get( cacheKey )
        if updates != None:
            s['updatesDay'] = int(updates)
        else:
            s['updatesDay'] = int(0)

        cacheKey = "key4-sensorTokenBucketWindow%s/%s"%(s['name'],minute1)
        updates = memcache.get( cacheKey )
        if updates != None:
            s['updatesMin'] = int(updates)
        else:
            s['updatesMin'] = int(0)
            
        ip = findIPforSensorID( s['id'] )
        if ip:
            s['ip']=ip
                                     
    #sensors = sorted( sensors , cmp=lambda x,y: cmp( y['updates'], x['updates'] ) )
    sensors = sorted( sensors , key=lambda sensor: sensor['updatesDay'] , reverse=True )

    ipAddrs = findAllKnownIP()
    ips = []
    for ip in ipAddrs:
        cacheKey = "key4-ipTokenBucketMinute:%s/%s"%(ip,minute0)
        updates0 = memcache.get( cacheKey )
        if updates0 == None:
            updates0 = 0
        updates0 = int( updates0 )

        cacheKey = "key4-ipTokenBucketMinute:%s/%s"%(ip,minute1)
        updates1 = memcache.get( cacheKey )
        if updates1 == None:
            updates1 = 0
        updates1 = int( updates1 )
        
        ips.append( { 'ip':ip , 'updates0':updates0 , 'updates1':updates1 } )
        
    return render_to_response( template , { 'sensors':sensors,'ipAddrs':ips,
                                            'host':request.META["HTTP_HOST"] }) 



#@digestProtect(realm='fluffyhome.com') # TODO get from settings file 
@login_required()
def showGraphs( request, userName ):
    template = "showGraphs.html"
    
    sensors = findAllResourceSensors( findUserIDByName( userName ) )

    sensors = sorted( sensors , cmp=lambda x,y: cmp( x['label'], y['label'] ) )

    return render_to_response( template , { 'user':userName,
                                            'sensors':sensors,
                                            'host':request.META["HTTP_HOST"] }) 


#@digestProtect(realm='fluffyhome.com') # TODO get from settings file 
@login_required()
def patchHourly(request):
    val = hourlyPatch()
    return HttpResponse("<h1>Patched %d Hourly </h1>"%val)

#@digestProtect(realm='fluffyhome.com') # TODO get from settings file 
@login_required()
def patchHourlyCount(request):
    val = hourlyPatchCount()
    return HttpResponse("<h1>Counted %d hourly to patch</h1>"%val)


#@digestProtect(realm='fluffyhome.com') 
@login_required()
def resetSensors(request,userName):
    # reset all values, integrals, and energy readings for all the users sensor
    
    sensorsIDs = findAllSensorIdNamePairs( findUserIDByName( userName ) )
    for sensorData in sensorsIDs:
        sensorID = sensorData[0]
        storeMeasurement( sensorID , value=0.0 , reset=True )

    return HttpResponse("<h1>Reset all sensors</h1>")


#@digestProtect(realm='fluffyhome.com') 
@login_required()
def showPlotOLD_NO_USE(request,userName,sensorName):
    sensorID = findSensorID(userName,sensorName)
    if sensorID == 0 :
        logger.debug( "Sensor name %s not found"%sensorName )   
        return HttpResponseNotFound('<h1>For user=userName=%s sensor=%s not found</h1>'%(userName,sensorName) )  

    data = { 'sensorName': sensorName ,
             'user':userName,
             'label': getSensorLabelByID(sensorID),
             'host' : request.META["HTTP_HOST"] }
    return render_to_response('showPlot.html', data )


#@digestProtect(realm='fluffyhome.com') 
@login_required()
def showLineGraph(request,userName,sensorName):
    sensorID = findSensorID(userName,sensorName)
    if sensorID == 0 :
        logger.debug( "Sensor name %s not found"%sensorName )  
        return HttpResponseNotFound('<h1>For user=userName=%s sensor=%s not found</h1>'%(userName,sensorName) )  

    data = { 'sensorName': sensorName ,
             'user':userName,
             'label': getSensorLabelByID(sensorID),
             'host' : request.META["HTTP_HOST"] }
    return render_to_response('lineGraph.html', data )


##@digestProtect(realm='fluffyhome.com')  # TODO - fix this security nightmare 
@login_required()
def showLineGraphCSV(request,userName,sensorName):
    sensorID = findSensorID( userName, sensorName )
    if sensorID == None:
        logger.debug( "Sensor name %s not found"%sensorName )  
        return HttpResponseNotFound('<h1>user=%s stream name=%s not found</h1>'%(user,streamName) )  

    html = ""

    #  get users time zone from DB
    userID =  findUserIdByName( userName )
    assert userID > 0 
    userMeta = getUserMetaByUserID( userID )
    timeOffset = userMeta['timeZoneOffset']
    assert timeOffset != None

    # get most recent values
    query = Measurement2.objects
    query = query.filter( sensorID = sensorID )
    query = query.order_by("-time") #TODO - should have time based limits 
    measurements = query.all()[:1000] #TODO need to deal with more than 1000 meassurements

    measurements.reverse()

    prevTime = None
    prevValue = None

    for measurement in measurements:
       
        time = datetime.fromtimestamp( measurement.time ) + timedelta( hours=timeOffset ) 
        value = measurement.value
        
#        if prevTime is not None:
#            if time > prevTime + timedelta( seconds = 15 ) : 
#                # insert synthetic data point to carry prev value forward 
#                synTime = time - timedelta( seconds = 1 )
#                number = float( prevValue )
#                sample = "%s , %f \n"%( str(synTime.timetuple()[0:6]) , number )
#                html += sample
        try:
            number = float( value )
            #sample = " %s, %f \n"%( str(time.timetuple()[0:6]) , number )
            sample = " %f, %f \n"%(  float(measurement.time)*1000.0 , number )
            html += sample
            prevTime = time
            prevValue = value 

        except ValueError:
            logger.debug( "Non numberic value in measurement value=%s"%( str(value) ) )

    response = HttpResponse()
    #response = HttpResponse("text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s-%s.csv'%(userName,sensorName)
    response.write( html );
    return response 


##@digestProtect(realm='fluffyhome.com')  # TODO - fix this security nightmare 
@login_required()
def showPlotJson_OLD_NO_USE(request,userName,sensorName):
    sensorID = findSensorID( userName, sensorName )
    if sensorID == None:
        logger.debug( "Sensor name %s not found"%sensorName )  
        return HttpResponseNotFound('<h1>user=%s stream name=%s not found</h1>'%(user,streamName) )  

    html = ""
    html += "google.visualization.Query.setResponse({ \n"
    html += "version:'0.6',\n"
    # reqId:'0',status:'ok',sig:'6099996038638149313',
    html += "status:'ok', \n"
    html += "reqId:'0', \n"

    html += "table:{ cols:[ {id:'Time',label:'Time',type:'datetime'}, \n"
    html += "               {id:'Value',label:'KWh',type:'number'}], \n"
    html += "  rows:[ \n"

    #  get users time zone from DB
    userID =  findUserIdByName( userName )
    assert userID > 0 
    userMeta = getUserMetaByUserID( userID )
    timeOffset = userMeta['timeZoneOffset']
    assert timeOffset != None

    # get most recent values
    query = Measurement2.objects
    query = query.filter( sensorID = sensorID )
    query = query.order_by("-time") #TODO - should have time based limits 
    measurements = query.all()[:1000] #TODO need to deal with more than 1000 meassurements

    measurements.reverse()

    prevTime = None
    prevValue = None

    for measurement in measurements:
       
        time = datetime.fromtimestamp( measurement.time ) + timedelta( hours=timeOffset ) 
        value = measurement.value
        
        if prevTime is not None:
            if time > prevTime + timedelta( seconds = 15 ) : 
                # insert synthetic data point to carry prev value forward 
                synTime = time - timedelta( seconds = 1 )
                number = float( prevValue )
                sample = "   {c:[  {v:'Date%s'} , {v:'%f'}  ]},\n"%( str(synTime.timetuple()[0:6]) , number )
                html += sample

        try:
            number = float( value )
            sample = "   {c:[  {v:'Date%s'} , {v:'%f'}  ]}, \n"%( str(time.timetuple()[0:6]) , number )
            html += sample
            prevTime = time
            prevValue = value 

        except ValueError:
            logger.debug( "Non numberic value in measurement value=%s"%( str(value) ) )

    html += "  ] } \n" #close rows, then table
    html += "} );\n" #close whole object 

    #response = HttpResponse("text/plain")
    response = HttpResponse()
    #response['Content-Disposition'] = 'attachment; filename=somefilename.csv'
    response.write( html );

    return response 


def findValueByTimeSensorID( values, time, sid ):
    for v in values:
        if v.time == time:
            if v.sensorID == sid:
                return v
    return None


##@digestProtect(realm='fluffyhome.com') # TODO fix 
@login_required()
def usageJson(request,userName,sensorName,type,period):
    tqxParams = request.GET.get('tqx','')
    
    reqId = '0'
    try:
        params = dict( [part.split(':') for part in tqxParams.split(';') ] ) 
        reqId = params['reqId']
    except (ValueError,KeyError):
        pass

    logger.debug("usageJson reqId = %s"%reqId)

    now = long( time.time() )
    now = now - now%3600

    epoch = getUserSettingEpoch( userName )

    head = ""
    head += "google.visualization.Query.setResponse({ \n"
    head += "version:'0.6',\n"
    head += "status:'ok', \n"
    head += "reqId:'%s', \n"%reqId

    cacheKey = "key4-usageJson:%d/%s/%s/%s/%s/%d"%(epoch,userName,sensorName,type,period,now)
    id = memcache.get( cacheKey )
    #id = None # TODO - remove
    if id != None:
        response = HttpResponse()
        response.write( head )
        response.write( id )
        return response 

    #  get users time zone from DB
    userID =  findUserIdByName( userName )
    assert userID > 0 
    userMeta = getUserMetaByUserID( userID )
    timeOffset = userMeta['timeZoneOffset']
    assert timeOffset != None
    assert timeOffset <= 12.5, "time offset = %s "%timeOffset
    assert timeOffset >= -12.5, "time offset = %s "%timeOffset
    timeOffsetSeconds = int( 3600.0 * timeOffset ) 

    ret = ""
    ret += "table:{ cols:[ {id:'Time',label:'Time',type:'string'}, \n"

    sID =  findSensorID(userName,sensorName) 
    assert sID != 0 , "bad sensor ID for user=%s,sensor=%s"%(userName,sensorName)

    sensors = findAllResourceSensors( findUserIdByName( userName ) , sID ) #this returns an array of dictionaries

    for sensor in sensors:
        if sensor['group']:
            ret += "               {id:'%s',label:'Other %s',type:'number'}, \n"%(sensor['name'],sensor['label'])
        else:
            ret += "               {id:'%s',label:'%s',type:'number'}, \n"%(sensor['name'],sensor['label'])
    ret += "             ], \n" # close up cols array 
    ret += "  rows:[ \n"

    now = long( time.time() )
    now = now - now % 3600
    
    # default show last 12 hours 
    start = now - 12*3600
    end = now 
    step = 3600
    hour = None
    hourOfWeek = None
    
    if period == "day": 
        mid = now 
        start = mid - 24*3600
        end = mid 
        step = 3600
        hour = None

    if period == "0day": 
        mid = now - ( (now + timeOffsetSeconds )%(24*3600) ) # TODO deal with  and 4 am is new midnight
        start = mid 
        end = mid  + 24*3600
        step = 3600
        hour = None

    if period == "1day": 
        mid = now - ( (now + timeOffsetSeconds )%(24*3600) ) # TODO deal with  and 4 am is new midnight
        start = mid - 24*3600
        end = mid 
        step = 3600
        hour = None

    if period == "2day" :
        mid = now - ( (now + timeOffsetSeconds )%(24*3600) ) # TODO deal with  and 4 am is new midnight
        start = mid - 24*3600
        end = mid  + 24*3600
        step = 3600 
        hour = None

    if period == "7day":
        mid = now - ( (now + timeOffsetSeconds )%(24*3600) ) # TODO deal with  and 4 am is new midnight
        start = mid - 7*24*3600
        end = mid
        step = 3600 * 24 
        hour = (start/3600) % 24

    if period == "30day":
        mid = now - ( (now  + timeOffsetSeconds )%(24*3600) ) # TODO deal with  and 4 am is new midnight
        start = mid - 30*24*3600
        end = mid
        step = 3600 * 24 
        hour = (start/3600) % 24

    if period == "6week":
        mid = now - ( (now  + timeOffsetSeconds ) % (7*24*3600) ) # TODO deal with  and 4 am is new midnight
        start = mid - 6 * 7 *24*3600
        end = mid
        step = 3600 * 24 * 7
        hourOfWeek = (start/3600) % (24*7)
        hour = None

    if period == "Aug": # august this year - TODO - should be last AUG  
        mid = now - ( (now  + timeOffsetSeconds ) % (24*3600) ) # TODO deal with  and 4 am is new midnight
        mid   = time.mktime( ( time.localtime(mid)[0] , 9,1,1,0,0,0,0,0 ) )
        start = time.mktime( ( time.localtime(mid)[0] , 8,1,1,0,0,0,0,0 ) ) 
        end   = mid
        step = 3600 * 24 * 7
        hour = (start/3600) % 24

    logger.debug( "start=%f end=%f"%(start,end) )


    userID =  findUserIdByName( userName )
    assert userID > 0 

    #  get all costs from DB
    userMeta = getUserMetaByUserID( userID )

    # get all the hourly values from the database
    values = getHourlyByUserIDTime( userID, start, end , hour, hourOfWeek )

    start = long( start )
    end = long( end )
    step = long( step )
    
    for t in range( start , end, step ):
        ret += "   {c:[  \n"

        localTime = datetime.fromtimestamp( t ) + timedelta( hours=timeOffset ) 
        if ( step == 3600 ): # hour
            ret += "        {v:'%02d:00'}, \n"%( localTime.hour ) 
        elif ( step == 24*3600 ): # day 
            ret += "        {v:'%s'}, \n"%(  localTime.strftime("%a") )
        elif ( step == 7*24*3600 ): # week 
            ret += "        {v:'W-%s'}, \n"%(  localTime.strftime("%U") )
        else:
            assert 0

        for sensor in sensors:
            sensorID = int( sensor['id'] )
            assert sensorID > 0
             
            start = None
            end = None
            startI = None
            endI = None

            value = findValueByTimeSensorID( values , t , sensorID )
            if value is not None:
                if sensor['group'] is True:
                    start = value.groupOtherEnergy 
                else:
                    start = value.energy
                    startI = value.integral

            value = findValueByTimeSensorID( values , t+step , sensorID )
            if value is not None:
                if sensor['group'] is True:
                    end = value.groupOtherEnergy 
                else:
                    end = value.energy
                    endI = value.integral

            v = 0.0 
            if (start is not None) and (end is not None):
                v = end-start
            if ( v < 0 ) : # energy can go negative when a reset of a counter happens - this ignores that
                v = 0

            vI = 0.0 
            if (startI is not None) and (endI is not None):
                vI = endI - startI
            if ( vI < 0 ) : # integral can go negative when a reset of a counter happens - this ignores that
                vI = 0

            if not ( v == v ): # nan
                v = 0.0
            if not ( vI == vI ): # nan
                vI = 0.0
                
            kWh = 0
            water = 0
            cost = 0
            co2 = 0

            kWh = v / (3600*1000.0 ) # convert J to kWh   

            if sensor['type'] == 'Water' :
                water = vI

            if type == "gas" :
                if sensor['type'] != 'Gas' :
                    kWh = 0
                    water=0

            if type == "water" :
                if sensor['type'] != 'Water' :
                    kWh = 0
                    water = 0

            if type == "elec" :
                if sensor['type'] != 'Electricity' :
                    kWh = 0
                    water =0

            if sensor['type'] == 'Gas' :
                cost = kWh * userMeta['gasCost'] 
                co2  = kWh * userMeta['gasCO2']

            if sensor['type'] == 'Electricity' :
                cost = kWh * userMeta['elecCost']
                co2  = kWh * userMeta['elecCO2']

            if sensor['type'] == 'Water' :
                cost = water * userMeta['waterCost']
                co2  = 0

            if   type == "cost" :
                ret += "        {v:%f}, \n"%( cost )
            elif type == "water" :
                ret += "        {v:%f}, \n"%( water )
            elif type == "co2" :
                ret += "        {v:%f}, \n"%( co2 )
            else: # this case for electircity and energy 
                ret += "        {v:%f}, \n"%( kWh )

        ret += "   ]}, \n" # close column arrary 

    ret += "  ] } \n" #close rows, then table
    ret += "} );\n" #close whole object 

    memcache.put( cacheKey, ret , 4*3600 )

    response = HttpResponse()
    response.write( head )
    response.write( ret )
    return response 
    


def generateJson( tqxParams, vals , label, userName ):
    reqId = '0'
    try:
        params = dict( [part.split(':') for part in tqxParams.split(';') ] ) 
        reqId = params['reqId']
    except (ValueError,KeyError):
        pass

   #  get users time zone from DB
    userID =  findUserIdByName( userName )
    assert userID > 0 
    userMeta = getUserMetaByUserID( userID )
    timeOffset = userMeta['timeZoneOffset']
    assert timeOffset != None

    html = ""
    html += "google.visualization.Query.setResponse({ \n"
    html += "version:'0.6',\n"
    # reqId:'0',status:'ok',sig:'6099996038638149313',
    html += "status:'ok', \n"

    html += "reqId:'%s', \n"%reqId

    html += "table:{ cols:[ {id:'Time',label:'Time',type:'string'}, \n"
    html += "               {id:'Value',label:'%s',type:'number'}], \n"%label
    html += "  rows:[ \n"
 
    for val in vals:
        time = val['time']
        avg = val['average']
        
        try:
            number = float( avg )
            # convert to local time 
            time = time + timedelta( hours=timeOffset )
            hour = time.hour
            sample = "   {c:[  {v:'%s:00'} , {v:%f}  ]}, \n"%( str(hour) , number )
            html += sample
        except ValueError:
            logger.debug( "Non numberic value in measurement value=%s"%( str(value) ) )

    html += "  ] } \n" #close rows, then table
    html += "} );\n" #close whole object 
    return html


##@digestProtect(realm='fluffyhome.com') # TODO fix 
@login_required()
def todayJson(request,userName,sensorName):
    sensorID = findSensorID(userName,sensorName)
    if sensorID == 0 :
        logger.debug( "Sensor name %s not found"%sensorName )  
        return HttpResponseNotFound('<h1>userName=%s stream name=%s not found</h1>'%(userName,sensorName) )  

    tqxParams = request.GET.get('tqx','')
    logger.debug( "foo=%s", tqxParams )
    
    #  get users time zone from DB
    userID =  findUserIdByName( userName )
    assert userID > 0 
    userMeta = getUserMetaByUserID( userID )
    timeOffset = userMeta['timeZoneOffset']
    assert timeOffset != None

    #vals = getDayValues( userName,sensorName, datetime.utcnow() )
    sensorID = findSensorID( userName,sensorName )
    assert sensorID > 0 # TODO should html erro 

    utime = long( time.time() )
    utime = utime - utime % 3600 # get prev hour time 
    vals = []
    for i in range(-24,0):
    #for i in range(-34*24,-33*24):
        #ptime = datetime.utcnow() + timedelta( hours=i )
        #startTime = datetime( ptime.year, ptime.month, ptime.day, ptime.hour )
        #timeTuple = startTime.timetuple()
        #floatTime =  time.mktime( timeTuple )
        #utime = long( floatTime )

        t = utime + i*3600 # is is negative so add it 
        #t = utime + 24*i*3600 # is is negative so add it 
        dTime = datetime.fromtimestamp( t )

        v = 7000
        start = getHourlyIntegralBySensorID( sensorID, t)
        end   = getHourlyIntegralBySensorID( sensorID ,t+3600)
        #end   = getHourlyIntegralBySensorID( sensorID ,t+24*3600)
        if ( start is not None ) and ( end is not None ):
            if ( end >= start ) and ( start >= 0 ):
                v = (end-start) / 3600.0
                #v = (end-start) / (24 * 3600.0)
#        if (  end < start ) :
#            v = 3000 # TODO ver bad
#        if (  start < 0 ) :
#            v = 5000 # TODO ver bad
#        if ( v > 5000 ):
#            v = 10000 # TODO VERY BAD 
#        if ( v < 0 ):
#            v = 15000 # TODO VERY BAD 
        logger.debug("sensor=%s hour=%d start=%s end=%s i=%s v=%s"%( getSensorLabelByID(sensorID),
                                                                      (t/3600) % 24 ,
                                                                      start,end,i,v ) )

        dict = { 'time': dTime, 'average': v } 
        vals.append( dict )

    html = generateJson( tqxParams, vals  , 
                         "Avg %s (%s)"%( getSensorLabelByID(sensorID), getSensorUnitsByID(sensorID) ), 
                         userName )

    response = HttpResponse()
    response.write( html );
    return response 


def graphWindToday(request,sensorName):
    userName='wind'
    sensorID = findSensorID( userName, sensorName )
    if sensorID == 0 :
        logger.debug( "Sensor name %s not found"%sensorName )  
        return HttpResponseNotFound('<h1>userName=%s sensor name=%s not found</h1>'%(userName,sensorName) )

    data = { 'sensorName': sensorName ,
             'user': None,
             'graphUser':userName,
             'label': getSensorLabelByID(sensorID),
             'host' : request.META["HTTP_HOST"] }
    return render_to_response('graphTodaySmall.html', data )


#@digestProtect(realm='fluffyhome.com') 
@login_required()
def graphToday(request,userName,sensorName):
    sensorID = findSensorID( userName, sensorName )
    if sensorID == 0 :
        logger.debug( "Sensor name %s not found"%sensorName )  
        return HttpResponseNotFound('<h1>userName=%s sensor name=%s not found</h1>'%(userName,sensorName) )

    data = { 'sensorName': sensorName ,
             'user': userName,
             'graphUser':userName,
             'label': getSensorLabelByID(sensorID),
             'host' : request.META["HTTP_HOST"] }
    return render_to_response('graphToday.html', data )


#@digestProtect(realm='fluffyhome.com') 
@login_required()
def dumpAlarm(request,userName,year,day):
    logger.debug( "dumping alarm for %s %s %s"%(userName,year,day ) )

    year = int( year )
    day = int( day )
    
    response = HttpResponse(mimetype='application/xml')
    response['Content-Disposition'] = 'attachment; filename=dump-%s-%s-%0d-%03d.xml'%(userName,'alarm',year,day)
    
    response.write( "<dump-alarm>\n" )

    t = int( time.mktime( ( year , 1,1,0,0,0,0,0,0 ) ) ) - time.timezone
    t = t + day * 24 * 3600
    start = t
    end = t + 24*3600 

    if ( userName == 'fluffy' ):
        alarms = findAlarmsBetween( 3261 , start, end ) # TODO , don't hard code alarm ID for user 
        for a in alarms:
            if a.notCrit is None:
                if a.crit == 5:
                    a.notCrit = 1
                else:
                    a.notCrit = 0 
            ad="<alarm time='%d' id='%d' eq='%d' code='%d' part='%d' crit='%d' zone='%d' user='%d' note='%s' notCrit='%d' />\n"%(
                a.time,a.alarmID, a.eq, a.code, a.part, a.crit, a.zone, a.user, a.note, a.notCrit )
            response.write( ad )
            
    response.write( "</dump-alarm>\n" )
    return response

            
#@digestProtect(realm='fluffyhome.com') 
@login_required()
def dumpSensor(request,userName,sensorName,year,day):
    logger.debug( "dumping sensor for %s %s %s %s"%(userName,sensorName,year,day ) )

    year = int( year )
    day = int( day )
    
    response = HttpResponse(mimetype='application/xml')
    response['Content-Disposition'] = 'attachment; filename=dump-%s-%s-%0d-%03d.xml'%(userName,sensorName,year,day)
    
    response.write( "<dump-sensor>\n" )

    sensorID = findSensorID( userName , sensorName )
    assert sensorID is not None
    assert sensorID != 0

    t = int( time.mktime( ( year , 1,1,0,0,0,0,0,0 ) ) ) - time.timezone
    t = t + day * 24 * 3600
    start = t
    end = t + 24*3600 
    
    measurements = findMeasurementsBetween( sensorID, start, end  )
    for m in measurements:
        md="<measurement user='%s' sensor='%s' time='%d' "%(
            userName, sensorName, m.time, )
        if m.value != None:
            if m.value == m.value: # test NaN
                md += "value='%f' "%m.value
        if m.integral != None:
            if m.integral == m.integral: # test NaN
                md += "integral='%f' "%m.integral
        if m.energy != None:
            if m.energy == m.energy: # test NaN
                md += "energy='%f' "%m.energy
        if m.patchLevel != None:
            md += "patchLevel='%d' "%m.patchLevel
        md += "/>\n"
        response.write( md )

    response.write( "</dump-sensor>\n" )
    return response           


@login_required()
def dumpMeta(request):
    response = HttpResponse(mimetype='application/xml')
    response['Content-Disposition'] = 'attachment; filename=all-dump.xml'
    response.write( "<dump-meta>\n" )

    usersNames = findAllUserNames()
    for userName in usersNames:
        dumpUserData( userName, response )

        sensors = findAllSensorsByUserID( findUserIdByName( userName ) )
        for sensor in sensors:
            dumpSensorData( sensor, response )

    response.write( "</dump-meta>\n" )
    return response


#@digestProtect(realm='fluffyhome.com') 
@login_required()
def dumpUser(request,userName):
    response = HttpResponse(mimetype='application/xml')
    response['Content-Disposition'] = 'attachment; filename=%s-dump.xml'%userName

    response.write( "<dump>\n" )

    user = findUserByName( userName )
    dumpUserData( userName, response )

    sensors = findAllSensorsByUserID( findUserIdByName( userName ) )
    for sensor in sensors:
        dumpSensorData( sensor, response )
             
        measurements = findRecentMeasurements( sensor.sensorID )
        for m in measurements:
            md="<measurement user='%s' sensor='%s' time='%d' "%(
                userName, sensor.sensorName, m.time, )
            if m.value != None:
                if m.value == m.value: # test NaN
                    md += "value='%f' "%m.value
            if m.integral != None:
                if m.integral == m.integral: # test NaN
                    md += "integral='%f' "%m.integral
            if m.energy != None:
                if m.energy == m.energy: # test NaN
                    md += "energy='%f' "%m.energy
            if m.patchLevel != None:
                md += "patchLevel='%d' "%m.patchLevel
            md += "/>\n"
            response.write( md )

    if ( userName == 'fluffy' ):
        alarms = findRecentAlarmData( 3261 ) # TODO , don't hard code alarm ID for user 
        for a in alarms:
            if a.notCrit is None:
                if a.crit == 5:
                    a.notCrit = 1
                else:
                    a.notCrit = 0 
            ad="<alarm time='%d' id='%d' eq='%d' code='%d' part='%d' crit='%d' zone='%d' user='%d' note='%s' notCrit='%d' />\n"%(
                a.time,a.alarmID, a.eq, a.code, a.part, a.crit, a.zone, a.user, a.note, a.notCrit )
            response.write( ad )
        
    response.write( "</dump>\n" )

    return response


def dumpUserData( userName, response ):
    user = findUserByName( userName ) 
    response.write( "<user userID='%d' userName='%s' \n"%( user.userID, user.userName, ) )
    response.write( "   email='%s' "%( user.email ) )
    response.write( "   email2='%s' "%( user.email2 ) )
    response.write( "   email3='%s' "%( user.email3 ) )
    response.write( "   sms1='%s' "%( user.sms1 ) )
    response.write( "   timeZoneOffset='%f' "%( user.timeZoneOffset ) )
    response.write( "   gasCost='%f' "%( user.gasCost ) )
    response.write( "   elecCost='%f' "%( user.elecCost ) )
    response.write( "   waterCost='%f' "%( user.waterCost ) )
    response.write( "   gasCO2='%f' "%( user.gasCO2 ) )
    response.write( "   elecCO2='%f' >\n"%( user.elecCO2 ) )

    #d = user.to_xml()  # This includes the users password 
    #response.write( d )
    response.write( "</user>\n" )


def dumpSensorData( sensor, response ):
        if sensor.groupTotal is None: 
            sensor.groupTotal=False
        if sensor.ignore is None: 
            sensor.ignore=False

        attr = ""
        attr += " sensorID='%d'"%sensor.sensorID 
        attr += " sensorName='%s'"%sensor.sensorName 
        attr += " label='%s'"%sensor.label 

        attr += " userID='%d'"%sensor.userID
        if sensor.userID is not None:
            attr += " userName='%s'"%findUserNameBySensorID( sensor.sensorID )
            
        attr += " public='%d'"%sensor.public 
        attr += " hidden='%d'"%sensor.hidden
        attr += " ignore='%d'"%sensor.ignore 
        attr += " groupTotal='%d'"%sensor.groupTotal 
        attr += " killed='%d'"%sensor.killed 

        attr += " category='%s'"%sensor.category 
        attr += " type='%s'"%sensor.type 

        attr += " units='%s'"%sensor.units 
        if sensor.unitsWhenOn is not None:
            attr += " unitsWhenOn='%s'"%sensor.unitsWhenOn 

        if sensor.displayMin is not None:
            attr += " displayMin='%f'"%sensor.displayMin 
        if sensor.displayMax is not None:
            attr += " displayMax='%f'"%sensor.displayMax 

        attr += " inGroup='%s'"%sensor.inGroup 
        if sensor.inGroup is not None:
            if sensor.inGroup > 0:
                attr += " inGroupName='%s'"%getSensorNamelByID(sensor.inGroup)

        if sensor.watts is not None:
            attr += " watts='%f'"%sensor.watts 
        if sensor.valueWhenOn is not None:
            attr += " valueWhenOn='%f'"%sensor.valueWhenOn 
        if sensor.threshold is not None:
            attr += " threshold='%f'"%sensor.threshold 

        if sensor.maxUpdateTime is not None:
            attr += " maxUpdateTime='%f'"%sensor.maxUpdateTime 

        response.write( "<sensor %s >\n"%attr )
        #d = sensor.to_xml()
        #response.write( d )
        response.write( "</sensor>\n" )

        

class EditSensorForm(forms.ModelForm):
    #inGroup = forms.TypedChoiceField( coerce=int )
    inGroup2 = forms.TypedChoiceField( coerce=int )
    class Meta:
        model = Sensor
        exclude = [ 'sensorID','userID','sensorName','inGroup','apiKey','tags','watts','public','killed','displayMin','displayMax' ]
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.fields['inGroup2'].choices = findAllGroupsIdNamePairs( kwargs['instance'].userID )


        

#@digestProtect(realm='fluffyhome.com') 
@login_required()
def editSensor(request,userName,sensorName):
    sensorID = findSensorID(userName,sensorName)
    if sensorID == 0 :
        logger.debug( "Sensor name %s not found"%sensorName )  
        return HttpResponseNotFound('<h1>userName=%s stream name=%s not found</h1>'%(userName,sensorName) )
    
    record = findSensor( sensorID ,"editSensor")
    assert record is not None, "can't find record in DB"

    sensorData = { 'user': userName , 'streamName': sensorName , 'category':record.category }
    msg = "Edit any values you wish to change above then press Update"

    if request.method == 'POST': 
        form = EditSensorForm(request.POST, instance=record)
        if form.is_valid():
            logger.debug( "input form IS valid" )
            info = form.save(commit=False)

            x = form.clean()
            group =  x['inGroup2']
            #logger.debug( "inGroup2 = %s"%( group ))
            record.inGroup = group
            
            if record.sensorName == "All":
                record.inGroup = 0

            record.save()
            updateUserSettingsEpoch(userName)
            msg ="Data succesfully saved"
        else:
            logger.error( "Error in form data to edit sensor form=%s"%( str( form )) )
            msg = "Some problem processing form"
    else:
        initVals =  { 'category':record.category,
                      'inGroup2': record.inGroup,
                     'label':record.label,
                     'hidden':record.hidden,
                     'ignore':record.ignore,
                     'units':record.units,
                     'type':record.type,
                     'groupTotal':record.groupTotal,
                     'unitsWhenOn':record.unitsWhenOn,
                     'valueWhenOn':record.valueWhenOn,
                     'threshold':record.threshold,
                     'maxUpdateTime':record.maxUpdateTime
                      }
        form = EditSensorForm( initVals, instance=record, auto_id=False  )

    #logger.debug( "debug for form=%s"%form )
    return render_to_response('editSensor.html', { 'msg':msg, 
                                             'form':form,
                                             'sensor': sensorData,
                                             'user':userName, 
                                             'host' : request.META["HTTP_HOST"] } )


#@digestProtect(realm='fluffyhome.com') 
#@login_required()
def createSensor(request,userName,sensorName):

    userID = findUserIDByName( userName  )
    assert userID > 0

    sensorID = findSensorID(userName,sensorName,create=True)
    assert sensorID > 0

    record = findSensor( sensorID ,"createSensor" )
    assert record is not None, "can't find record in DB"

    if request.method == 'POST': 
        #logger.debug( "POST data is %s"%str(request.POST) ) 
        data = request.POST

        record.label = data.get("label");
        record.category = data.get("category");
        record.type = data.get("type")
        record.groupTotal = ( data.get("groupTotal") == "1" );
        record.public = ( data.get("public") == "1" );
        record.hidden = ( data.get("hidden") == "1" );
        record.ignore = ( data.get("ignore") == "1" );
        if "units" in data:
            if data.get("units") != "None":
                record.units = data.get("units");
        if "displayMin" in data:
            if data.get("displayMin") != "None":
                record.displayMin = float( data.get("displayMin") );
        if "displayMax" in data:
            if data.get("displayMax") != "None":
                record.displayMax = float( data.get("displayMax") );
                
        if "watts" in data:
            if data.get("watts") != "None":
                record.watts = float( data.get("watts") );
        if "threshold" in data:
            if data.get("threshold") != "None":
                record.threshold = float( data.get("threshold") );
                
        if "maxUpdateTime" in data:
            if data.get("maxUpdateTime") != "None":
                record.maxUpdateTime = int( data.get("maxUpdateTime") );
                
        if "unitsWhenOn" in data:
            if data.get("unitsWhenOn") != "None":
                record.units = data.get("unitsWhenOn");
        if "valueWhenOn" in data:
            if data.get("valueWhenOn") != "None":
                record.watts = float( data.get("valueWhenOn") );

        if "inGroupName" in data:
            groupName = data.get("inGroupName")
            groupID = findSensorID(userName,groupName,create=True)
            record.inGroup = groupID

        record.save()
        updateUserSettingsEpoch(userName)
            
        return HttpResponse('<h1>Updated sensor %s</h1>'%sensorName  )  

    logger.debug( "Problem creating sensor %s"%sensorName )  

    return HttpResponseNotFound('<h1>Problem with create sensor %s </h1>'%( sensorName ) )



def loadAllSensors(request,userName):
    # check user exists 
    if findUserIdByName(userName) == 0 :
        logger.debug( "Problemfinding users %s"%userName )  
        return HttpResponseNotFound('<h1>Error: No user with name %s </h1>'%(userName) )  

    sensorsIDs = findAllSensorsIDsByUserID( findUserIdByName( userName ) )

    for s in sensorsIDs:
        assert s > 0
        meta = findSensorMetaByID( s ,"showAllSensors" );

    return HttpResponse('<h1>Updated sensor cache for user %s </h1>'%(userName) )  


def showAllWindSensors(request):
    # check user exists
    userName = 'wind'
    if findUserIdByName(userName) == 0 :
        logger.debug( "Problemfinding users %s"%userName )  
        return HttpResponseNotFound('<h1>Error: No user with name %s </h1>'%(userName) )  

    sensorDataList = []

    allGroupSensorID = findSensorID(userName,"All",create=True)
    assert allGroupSensorID > 0, "There is no group named 'All' for user %s"%userName

    sensorsIDs = findAllSensorsIDsByUserID( findUserIdByName( userName ) )
    
    # find all the groups in sorted order 
    groupList = []
    for s in sensorsIDs:
        assert s > 0
        meta = findSensorMetaByID( s ,"showAllWindSensors" );

        if meta['category'] == "Group":
                groupList.append( (meta['label'],s) )
    groupList = sorted( groupList )

    # if any sensor is not in any group, put it in the All group
    for s in sensorsIDs:
        meta = findSensorMetaByID( s ,"showAllWindSensors 1" );
        if meta['sensorName'] == "All": # don't put the All group in itself 
            meta['inGroup'] = 0
            continue
        found = False
        for group in groupList:
            if group[1] == meta['inGroup']:
                found = True
                break
        if not found:
            # this sensor is not in a valid group, move to all 
            meta['inGroup'] = allGroupSensorID
            logger.warning( "Moved sensor %s to All group"%meta['sensorName'] )

    # for each group, output it's tab then all the sensors/groups in it in sorted order 
    outList = []
    for group in groupList:
        grpID = group[1]

        # add this group as a tab 
        outList.append( (grpID,1) )

        # find and sort the sensors in this group 
        sList = []
        for s in sensorsIDs:
            meta = findSensorMetaByID( s ,"showAllWindSensors 2" )
            if meta['inGroup'] == grpID:
                if meta['units'] == 'km/h':
                    sList.append( (meta['label'],s) )

        slist = sorted( sList )
        for pair in sList:
            outList.append( (pair[1],0) )

    sensorData = {}
    sensorData['user'] = userName
    sensorData['label'] = 'Wind'
    sensorData['category'] = "Tab"
    sensorDataList.append( sensorData )
    
    # output all the stuff in the outlist paying attention to tags 
    for sensorPair in outList:
        sensorID = sensorPair[0]
        meta = findSensorMetaByID( sensorID ,"showAllWindSensors 3" )

        if meta['killed']:
            continue

        sensorData = {}
        sensorData['user'] = userName
        sensorData['name'] = meta['sensorName']
        sensorData['label'] = meta['label']
        sensorData['type'] = meta['type']
        sensorData['units'] = meta['units']
        sensorData['category'] = meta['category']
       
        if sensorPair[1] == 1:
            sensorData['category'] = "Tab"
        else:
            if sensorData['category'] != "Group":
                v = None
                v = getSensorValue( sensorID ) 
                if v is not None:
                    sensorData['value'] = int( round( v , 0 ) )
                else:
                    sensorData['value'] = "N/A"
                    sensorData['units'] = ""

                # get the time sensor
                name = string.replace( meta['sensorName'], "-speed" , "-time" )
                sensorID = findSensorID( 'wind' , name );
                v1 = None
                v1 = getSensorValue( sensorID ) 
                if v1 is not None:
                    sensorData['timeMin'] = '%02d'%( int( round( v1 , 0 ) )%100  )
                    sensorData['timeHour'] = '%d'%( int( round( v1 , 0 ) )/100  )

                # get the temp sensor
                name2 = string.replace( meta['sensorName'], "-speed" , "-temp" )
                sensorID2 = findSensorID( 'wind' , name2 );
                v2 = None
                v2 = getSensorValue( sensorID2 ) 
                if v2 is not None:
                    sensorData['temp'] = int( round( v2 , 0 ) )

                sensorDataList.append( sensorData )

    template = "feedsWindCompact.html"
    return render_to_response( template , { 'user':None,
                                            'pipeList': sensorDataList ,
                                            'host':request.META["HTTP_HOST"] }) 

#@digestProtect(realm='fluffyhome.com') 
@login_required()
def showAllSensors(request,userName):
    return showAllSensorsFunc(request,userName=userName)


@login_required()
def showAllSensorsFunc(request,userName):
    # check user exists 
    if findUserIdByName(userName) == 0 :
        logger.debug( "Problem finding users %s"%userName )  
        return HttpResponseNotFound('<h1>Error: No user with name %s</h1>'%(userName) )  

    sensorDataList = []

    allGroupSensorID = findSensorID(userName,"All",create=True)
    assert allGroupSensorID > 0, "There is no group named 'All' for user %s"%userName

    sensorsIDs = findAllSensorsIDsByUserID( findUserIdByName( userName ) )

    #logger.debug( "Found sernsor id len=%s "% len( sensorsIDs ) )  
    #logger.debug( "Found sernsor id %s "%str( sensorsIDs ) )
    
    # find all the groups in sorted order 
    groupList = []
    for s in sensorsIDs:
        assert s > 0
        meta = findSensorMetaByID( s ,"showAllSensors" );

        if meta['category'] == "Group":
                groupList.append( (meta['label'],s) )
    groupList = sorted( groupList )

    # if any sensor is not in any group, put it in the All group
    for s in sensorsIDs:
        meta = findSensorMetaByID( s ,"showAllSensors 1" );
        if meta['sensorName'] == "All": # don't put the All group in itself 
            meta['inGroup'] = 0
            continue
        found = False
        for group in groupList:
            if group[1] == meta['inGroup']:
                found = True
                break
        if not found:
            # this sensor is not in a valid group, move to all 
            meta['inGroup'] = allGroupSensorID
            logger.warning( "Moved sensor %s to All group"%meta['sensorName'] )

    # for each group, output it's tab then all the sensors/groups in it in sorted order 
    outList = []
    for group in groupList:
        grpID = group[1]

        # add this group as a tab 
        outList.append( (grpID,1) )

        # find and sort the sensors in this group 
        sList = []
        for s in sensorsIDs:
            meta = findSensorMetaByID( s ,"showAllSensors 2" );
            if meta['inGroup'] == grpID:
                    sList.append( (meta['label'],s) )

        slist = sorted( sList )
        for pair in sList:
            outList.append( (pair[1],0) )

    # output all the stuff in the outlist paying attention to tags 
    for sensorPair in outList:
        sensorID = sensorPair[0]
        meta = findSensorMetaByID( sensorID ,"showAllSensors 3" );

        if meta['killed']:
            continue

        sensorData = {}

        sensorData['user'] = userName

        sensorData['name'] = meta['sensorName']
        sensorData['label'] = meta['label']
        sensorData['type'] = meta['type']
        sensorData['units'] = meta['units']
        sensorData['category'] = meta['category']
       
        if sensorPair[1] == 1:
            sensorData['category'] = "Tab"
            total = 0 
            sum = 0
            total = findSensorPower( sensorID ) 
            sum = findGroupPower( sensorID , None, set() ) 
            if ( total-sum != 0 ): # add an other group
                sensorDataList.append( copy.deepcopy(sensorData) )
                sensorData['category'] = "Group"
                sensorData['label'] = "Other"
                sensorData['value'] = total - sum
        else:
            if sensorData['category'] == "Group":
                sensorData['value'] = findSensorPower( sensorID ) 
                sensorData['units'] = "W"
            if sensorData['category'] != "Group":
                v = None
                v = getSensorValue( sensorID ) 
                if v is not None:
                    t = getSensorLastTime( sensorID )
                    if t is not None:
                        sensorData['time'] = datetime.fromtimestamp(t)
                    sensorData['value'] = v
                    if sensorData['units'] == "%" :
                        if  v <= 1.0 : # evil percent hack TODO 
                            sensorData['value'] = 100 * v
                    if sensorData['units'] == "Pa" :
                        if  90000 < v and v < 150000 : # 13 to 20 PSI 
                            sensorData['value'] = round( v / 1000 , 1)
                            sensorData['units'] = "kPa"
                        else :
                            sensorData['value'] = round( v * 0.000145037738 , 1 )
                            sensorData['units'] = "psi"
                    if sensorData['units'] == "V" :
                        sensorData['value'] = round( v , 1 )
                    if sensorData['units'] == "RH%" :
                        sensorData['value'] = round( v , 1 )
                    if sensorData['units'] == "C" :
                        sensorData['value'] = round( v , 1 )

                         
                    e = getSensorLastEnergy( sensorID  ) 
                    if e is not None:
                        sensorData['energy'] = e / (3600.0 * 1000.0) # convert J to kWH
                    i = getSensorLastIntegral( sensorID ) 
                    if i is not None:
                        sensorData['integral'] = i
                    if (i is not None) and ( (sensorData['units'] == "lpm") or  (sensorData['units'] == "lps") ):
                        sensorData['secValue'] = i
                        sensorData['secUnits'] = "l"
                else:
                    sensorData['value'] = "N/A"
                    sensorData['units'] = ""
                if sensorData['units'] != "W":
                    watts = 0.0
                    watts = getSensorPower( sensorID ) 
                    if watts != 0.0:
                        sensorData['watts'] = watts
        sensorDataList.append( sensorData )

    template = "feedsCompact.html"
    return render_to_response( template , { 'user':userName,
                                            'pipeList': sensorDataList ,
                                            'host':request.META["HTTP_HOST"] }) 



#@digestProtect(realm='fluffyhome.com') 
@login_required()
def usage(request,userName):
    #TODO erro bad user 

    # check user exists 
    userID = findUserIdByName(userName)
    if userID == 0 :
        logger.debug( "Problem finding users %s"%userName )  
        return HttpResponseNotFound('<h1>Error: No user with name %s</h1>'%(userName) )  

    # TODO , add proper checks for user/sensor exists for all pages 

    assert type( userID ) is long, "Wrong user of of type %s"%( type(userID) )

    #  get all costs from DB
    userMeta = getUserMetaByUserID( userID )

    # TODO - rounding for display is lame and sort of wrong 

    sensorID =  findSensorID( userName, "All")
    assert sensorID != 0, "Group 'All' does not exist for user %s"%userName

    hydro =findSensorWater( sensorID , "Water" ) #  this is in l/s
    elec = findSensorPower( sensorID, "Electricity" )
    gas =  findSensorPower( sensorID , "Gas" )

    vars = {}
    vars['host'] = request.META["HTTP_HOST"]
    vars['user'] = userName

    #TODO move water to hydro 

    vars['waterCostPh'] = hydro*3600 * userMeta['waterCost'] 

    vars['gaskW']  = int(gas)/1000.0 #TODO fix round
    vars['gasCostPh'] = gas/1000 * userMeta['gasCost'] 
    vars['gasC02kgph'] = gas/1000 * userMeta['gasCO2']

    vars['eleckW'] = int(elec)/1000.0  #TODO fix round
    vars['elecCostPh'] = elec/1000 * userMeta['elecCost']
    vars['eleckC02kgph'] = elec/1000 * userMeta['elecCO2']

    vars['hydroLpm'] = hydro*60

    vars['totCostPh'] = vars['gasCostPh'] + vars['elecCostPh'] + vars['waterCostPh']
    vars['totC02kgph'] = vars['gasC02kgph'] + vars['eleckC02kgph']

    # round for display 
    vars['totCostPh'] = int(  vars['totCostPh'] *100 ) / 100.0
    vars['totC02kgph'] =  int( vars['totC02kgph'] * 1000 ) / 1000.0

    return render_to_response('usage.html', vars )


class AddGroupForm(forms.Form):
    name = forms.RegexField( "^\w[\-\w]{0,64}$" ) 


#@digestProtect(realm='fluffyhome.com') 
@login_required()
def findSensorToEnroll(request,userName):
    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2
    sensors = findSensorsToEnroll( ip )

    msg = "" 
    
    if request.method == 'POST': 
        form = AddGroupForm(request.POST)
        if form.is_valid():
            logger.debug( "input form is valid" )

            x = form.clean()
            name = x['name']
            
            logger.debug( "add new group name = %s", name )
            msg = "Created new %s group"%name 
            updateUserSettingsEpoch(userName)

            sensorName = name 
            findSensorID( userName, sensorName, create=True , createGroup=True )
    
            return HttpResponseRedirect( "/sensor/%s/%s/meta/"%(userName,sensorName) )

        else:
            logger.error( "Error in the create group Name of '%s'"%( str( form )) )
            msg = "Group Name must only have alphanumeric, underscore, or dash and start with alphanumeric character"
            
    else:
        form = AddGroupForm()

    return render_to_response('enroll.html', { 'sensors':sensors,
                                               'user':userName,
                                               'msg':msg, 
                                               'form':form,
                                               'host' : request.META["HTTP_HOST"] } )
    


#@digestProtect(realm='fluffyhome.com') 
@login_required()
def addSensor(request,userName,sensorName):
    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2
    secret = "secretTODO"

    enrollSensor( ip, sensorName, userName, secret )
    findSensorID( userName, sensorName, create=True ) # TODO - rethink security of who gets to claim a sensor and when

    return HttpResponseRedirect( "/sensor/%s/%s/meta/"%(userName,sensorName) )




#######OLD OLLD OLD OLD OLD #######################################################################



def taskUpdateValues(userName,sensorName,t):
    logger.debug("In taskUpdateValues user=%s sensor=%s t=%s"%(userName,sensorName,t) )
    
    sensorID = getSensorIDByName( sensorName ) # TODO - should check userName too
    assert sensorID > 0

    assert t is not None
    assert t > 0

    t = t - t % 3600
    getHourlyEnergyBySensorID( sensorID , t )


@login_required()
def qTaskUpdate(userName,sensorName,t):
    assert False, "depeerate as uses q task "
    logger.info("qTaskUpdate: user=%s sensor=%s time=%s"%(userName,sensorName,t) )
 
    if userName == "*":
        users = findAllUserNames() 
        for u in users:
            #taskqueue.add(url="/tasks/update/%s/%s/%s/"%(u,sensorName,time) )
            qTaskUpdate( u , sensorName, t )
        return
        
    userID = findUserIDByName( userName )
    assert userID is not None

    if sensorName == "*":
        sensors = findAllSensorsByUserID(userID)
            # q the non groups for computation before the groups to speed stuff up 
        for sensor in sensors:
            if sensor.killed != True:
                if sensor.category != "Group":
                    taskqueue.add(url="/tasks/update/%s/%s/%s/"%( userName, sensor.sensorName , t) )
                    #qTaskUpdate( userName, sensor.sensorName , t )
        for sensor in sensors:
            if sensor.killed != True:
                if sensor.category == "Group":
                    taskqueue.add(url="/tasks/update/%s/%s/%s/"%( userName, sensor.sensorName , t) )
                    #qTaskUpdate( userName, sensor.sensorName , t )
        return   

    assert t is not None

    if t == "*":
        now = long( time.time() )
        now = now - now%3600

        for t in range( now-2*3600, now+1, 3600):
            #taskqueue.add( url="/tasks/update/%s/%s/%d/"%(user,sensorName,t) )
            qTaskUpdate( userName, sensorName , t )
        return   
    
    if t == 0:
        now = long( time.time() )
        now = now - now%3600
        t = now

    assert t > 0 
    taskUpdateValues(userName,sensorName,t)


@login_required()
def taskThinValues(userName,sensorName,t):
    logger.debug("In taskThinValues user=%s sensor=%s t=%s"%(userName,sensorName,t) )
    
    sensorID = getSensorIDByName( sensorName ) # TODO - should check userName too
    assert sensorID > 0

    assert t is not None
    t = long( t )
    assert t > 0

    now = long( time.time() )
    oneMonth = long( 1*30*24*3600 )

    if t + oneMonth*12 >= now :
        # this is bad - don't thin data this rencent
        logger.error( "Trying to thin too rcent data %s %s %s"%(userName,sensorName,t) )
        return

    thinMeasurements( sensorID , t )
    
    
    


@login_required()
def qTaskThin(userName,sensorName,t):
    assert False, "depricatea as uses q Task "
    logger.info("qTaskThin: user=%s sensor=%s time=%s"%(userName,sensorName,t) )

    #thinqueue = taskqueue.Queue( "thin" );
    
    if userName == "*":
        users = findAllUserNames() 
        for u in users:
            #taskqueue.add(url="/tasks/thin/%s/%s/%s/"%(u,sensorName,time) )
            qTaskThin( u , sensorName, t )
        return False
        
    userID = findUserIDByName( userName )
    assert userID is not None

    if sensorName == "*":
        sensors = findAllSensorsByUserID(userID)
            # q the non groups for computation before the groups to speed stuff up 
        for sensor in sensors:
            if sensor.killed != True:
                if sensor.category != "Group":
                    taskqueue.add(url="/tasks/thin/%s/%s/%s/"%( userName, sensor.sensorName, t) )
                    #qTaskThin( userName, sensor.sensorName , t )
        for sensor in sensors:
            if sensor.killed != True:
                if sensor.category == "Group":
                    taskqueue.add(url="/tasks/thin/%s/%s/%s/"%( userName, sensor.sensorName, t) )
                    #qTaskThin( userName, sensor.sensorName , t )
        return False 

    assert t is not None
    oneMonth = 1*30*24*3600

    if t == "*":
        now = long( time.time() )
        now = now - now%3600
        for t in range( now-2*3600-oneMonth*12 , now+1-oneMonth*12 , 3600):
            #taskqueue.add( url="/tasks/thin/%s/%s/%d/"%( userName,sensorName,t) )
            qTaskThin( userName, sensorName , t )
        return False 
    
    if t == "-":
        now = long( time.time() )
        now = now - now%3600
        for t in range( now-oneMonth*14 , now+1-oneMonth*12 , 3600): # Q tasks for time range 
            taskqueue.add( url="/tasks/thin/%s/%s/%d/"%( userName,sensorName,t ) )
            #qTaskThin( userName, sensorName , t )
        return False

    assert t > 0 
    taskThinValues(userName,sensorName,t)

    return True


@login_required()
def thinValues(request,userName,sensorName,pTime):
    assert Flase," depricate as uses q task "
    logger.info("TASK: Running task thinValues %s/%s/%s"%(userName,sensorName,pTime) )

    #if userName != "*" and sensorName != "*":
    #    if not streamExists(userName,sensorName) : # TODO fix 
    #        return HttpResponseNotFound('<h1>user=%s sensor name=%s not found</h1>'%(userName,sensorName) )
     
    didIt = qTaskThin( userName, sensorName, pTime )

    if didIt:
        logger.debug("TASK: did task thinValues %s/%s/%s"%(userName,sensorName,pTime) )
        return HttpResponse('<h1>Did the thin Values</h1>'  )  
    
    logger.debug("TASK: finished quwing sub tasks for thinValues %s/%s/%s"%(userName,sensorName,pTime) )
    return HttpResponse('<h1>Queued tasks to thin Values</h1>'  )  


@login_required()
def updateValues(request,userName,sensorName,pTime):
    assert Flase, "depricate as uses q task "
    logger.info("TASK: Running task updateValues %s/%s/%s"%(userName,sensorName,pTime) )

    #if userName != "*" and sensorName != "*":
    #    if not streamExists(userName,sensorName) : # TODO fix 
    #        return HttpResponseNotFound('<h1>user=%s sensor name=%s not found</h1>'%(userName,sensorName) )
     
    qTaskUpdate( userName, sensorName, pTime )

    logger.debug("TASK: completed task updateValues %s/%s/%s"%(userName,sensorName,pTime) )
    return HttpResponse('<h1>Queued tasks to updated Values</h1>'  )  



@login_required()
def updateNotify(request,userName,sensorName):
    logger.info("TASK: Running task updateNotify %s %s"%(userName,sensorName,) )

    if userName == "*" :
        users = findAllUserNames()
    else:
        users = [ userName ]

    for userName in users:
        if sensorName == "*":
            sensors = findAllSensorsByUserID( findUserIDByName( userName ) )
        else:
            sensors = [ findSensor( getSensorIDByName( sensorName ) ) ]

        for sensor in sensors: # do ones that are NOT a group
            if sensor.killed != True:
                if sensor.category != "Group":
                    checkNotify(userName, sensor.sensorName )

    logger.info("TASK: completed task updateNotify %s %s"%(userName,sensorName) )
    return HttpResponse('<h1>Completed tasks to updated Value</h1>'  )  


@login_required()
def checkNotify(userName, sensorName):
    logger.debug( "CheckNotify %s %s "%(  userName, sensorName  ) )

    assert userName != "*"
    assert sensorName != "*"
    
    sensorID = getSensorIDByName( sensorName )
    assert sensorID > 0
    
    meta = findSensorMetaByID( sensorID, callFrom="checkNotify" )

    if ( meta['maxUpdateTime'] != None ):
        now = long(  time.time() )
        lastTime = getSensorLastTime( sensorID )
        if ( now-lastTime >=  meta['maxUpdateTime'] ):
            # this sensor is frozen ...
            lastValue = getSensorValue( sensorID )
            if ( lastValue == lastValue ): # this checks if value is not NaN in python 2.5. Better to use isnan in python 2.6 and later 
                # sensor just went to frozen
                mTime = lastTime+1
                storeMeasurement( sensorID, float('nan'), mTime )
                logger.debug( "Sensor just went frozen %s %s "%(  userName, meta['sensorName']  ) )
                sendNotify(userName,  meta['sensorName'],
                           "Sensor %s is frozen"%( meta['label'] ), 
                           "Sensor %s stoped reporting %s minutes ago"%( meta['label'], (now-lastTime)/60.0 )
                           )


@login_required()
def sendNotify(userName, sensorName, summary, note ):
    userID =  findUserIdByName( userName )
    assert userID > 0 

    #  get all costs from DB
    userMeta = getUserMetaByUserID( userID )

    # TODO - send notifies on ohter emails and sms 
    if ( userMeta['email1'] ):
        # send email
        message = mail.EmailMessage(sender = "cullenfluffyjennings@gmail.com",
                                    subject = summary,
                                    to = userMeta['email1'],
                                    body = note)
        message.send()
        logger.debug( "Sent email To:%s Subject:%s Body:%s"%(  userMeta['email1'], summary, note ) )


                
@login_required()
def updateAllValuesNow(request):
    doUpdateAllValuesNow()
    return HttpResponse('<h1>Completed update all hourly values</h1>'  )  


def doUpdateAllValuesNow():
    users = findAllUserNames()
    for userName in users:
        now = long( time.time() )
        now = now - now % 3600
        for t in range( now - 12*3600, now+1, 3600 ):
            userID = findUserIDByName( userName )
            assert userID is not None
            sensors = findAllSensorsByUserID(userID)
            for sensor in sensors: # do ones that a NOT a group
                if sensor.killed != True:
                    if sensor.category != "Group":
                        taskUpdateValues( userName, sensor.sensorName , t )
                        logger.debug( "Updated %s/%s/%d"%(  userName, sensor.sensorName , (t-now)/3600 ) )
            for sensor in sensors: # do the ones that ARE a group
                if sensor.killed != True:
                    if sensor.category == "Group":
                        taskUpdateValues( userName, sensor.sensorName , t )
                        logger.debug( "Updated %s/%s/%d"%(  userName, sensor.sensorName , (t-now)/3600 ) )




@login_required()
def updateAllValues(request): # this is just like updateAllValues but it queues the tasks instead of doing them
    assert False, "depricated as uses qTask "
    users = findAllUserNames()
    for userName in users:
        now = long( time.time() )
        now = now - now % 3600
        for t in range( now - 12*3600, now+1, 3600 ):
            userID = findUserIDByName( userName )
            assert userID is not None
            sensors = findAllSensorsByUserID(userID)
            for sensor in sensors:  # do ones that a NOT a group
                if sensor.killed != True:
                    if sensor.category != "Group":
                        qTaskUpdate( userName, sensor.sensorName , t )
                        logger.debug( "Updated %s/%s/%d"%(  userName, sensor.sensorName , (t-now)/3600 ) )
            for sensor in sensors:  # do the ones that ARE a group
                if sensor.killed != True:
                    if sensor.category == "Group":
                        qTaskUpdate( userName, sensor.sensorName , t )
                        logger.debug( "Updated %s/%s/%d"%(  userName, sensor.sensorName , (t-now)/3600 ) )

    return HttpResponse('<h1>Completed update all hourly values</h1>'  )  




def about(request):
    ver = "TBD";
    try:
        ver = os.environ['SERVER_SOFTWARE']
    except:
        pass
    devel = ver.startswith("Development")

    #t = loader.get_template('about.html')
    #c = Context( { 
    #    'djangoVersion': "%s.%s.%s"%( DJANGO_VERSION[0],  DJANGO_VERSION[1], DJANGO_VERSION[2] ) ,
    #    'pythonVersion': "%s"%( sys.version ) ,
    #    'osVersion': "%s"%( ver ) ,
    #    'host':request.META["HTTP_HOST"] })
    #return HttpResponse(t.render(c), mimetype="application/xhtml+xml")

    return render_to_response('about.html' , { 
        'djangoVersion': "%s.%s.%s"%( DJANGO_VERSION[0],  DJANGO_VERSION[1], DJANGO_VERSION[2] ) ,
        'pythonVersion': "%s"%( sys.version ) ,
        'osVersion': "%s"%( ver ) ,
        'host':request.META["HTTP_HOST"] } )


#@digestProtect(realm='fluffyhome.com')  # old - should depricate 
def store(request,userName,sensorName):
    return storeNoAuth(request,userName,sensorName) 


def storeNoAuth(request,userName,sensorName): #old - should depricate 
    if request.method != 'PUT':
        logger.warning( "Must use PUT %s %s"%(userName,sensorName) )
        return HttpResponseForbidden('<h1>Must use method PUT</h1>' )  

    data = request.raw_post_data
    #TODO validate user input data here for security 
    
    sensorID = findSensorID( userName,sensorName )
    if sensorID == 0 :
        logger.warning( "Not a valid sensor %s %s"%(userName,sensorName) )        
        return HttpResponseForbidden('<h1>Not a Valid sensor</h1>' )  

    logger.debug( "Store user,sensor=%s,%s set to val=%s ip=%s "%(userName,sensorName,data,ip) )
    storeMeasurement( sensorID,data)
    return HttpResponse() # return a 200 


def postAlarmValues(request):
    enableQuota = True 

    ver = os.environ['SERVER_SOFTWARE']
    devel = ver.startswith("Development")
    if ( devel ): 
        enableQuota = False # disable quotas for development environment

    if request.method != 'POST':
        logger.debug( "must use post to update alarm" )        
        return  HttpResponseNotFound( "<H1>Must use a POST to update values</H1>" )

    data = request.raw_post_data

    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2

    now = long( time.time() )

    minute = now - now % 60 # make window 1 minutes long 
    cacheKey = "key4-ipTokenBucketMinute:%s/%s"%(ip,minute)
    token = memcache.incr( cacheKey, 60 )

    rateLimit = 100 # Max number of request per minute from each IP address
    if enableQuota and token >= rateLimit:
        if token == rateLimit:
            # should we log this or not
            logger.warning( "IP %s exceed per minute rate limit"%ip )
        logger.debug( "IP %s exceed per minute rate limit"%ip )  
        return HttpResponseForbidden( "<H1>User has exceed limit of %d requests per minute</H1>"%rateLimit )
        
    logger.debug("Got post of alarm values %s from %s count=%d"%(data,ip, token) )
    addKnownIP( ip )
    
    try:
        jData = json.loads( data )
    except ValueError:
        logger.debug( "JSON data had error in parse")
        return HttpResponseNotFound( "<H1>JSON data had error in parse</H1><br /><pre>%s</pre>"%data )
    
    try:
        #TODO validate user input data here for security 
        logger.debug("j=%s"%str(jData) )
        logger.debug(" type is =%s"%str(type(jData)) )
        
        if ( type(jData) != dict ):
            logger.debug( "JSON data was not an object" )        
            return HttpResponseNotFound( "<H1>JSON data was not an object</H1>" )

        account = 0
        user = 0
        code = 0
        zone = 0
        eq = 0
        part = 0
        note = None

        if jData.has_key('a'):
            account = long( jData['a'] )
        if jData.has_key('u'):
            user = long( jData['u'] )
        if jData.has_key('c'):
            code = long( jData['c'] )
        if jData.has_key('z'):
            zone = long( jData['z'] )
        if jData.has_key('p'):
            part = long( jData['p'] )
        if jData.has_key('eq'):
            eq = long( jData['eq'] )
        if jData.has_key('n'):
            note = str( jData['n'] )
            
        day = now - now % (24*3600) # make window 24 hours long  
        cacheKey = "key4-alarmTokenBucketDay%s/%s"%(account,day)
        token = memcache.incr( cacheKey , 24*3600 )
        win = now - now % (60) # make window 1 min long  
        cacheKey = "key4-alarmTokenBucketWindow%s/%s"%(account,win)
        token = memcache.incr( cacheKey , 60 )
        
        rateLimit = 20 # Max number of request per minute from each sensor
        if enableQuota and token >= rateLimit:
            if token == rateLimit:
                # should we log this or not
                logger.warning( "IP %s exceed per minute rate limit for alarm updates"%ip )
                return HttpResponseForbidden( "<H1>User has exceed limit of %d updates per minute for alarm</H1>"%rateLimit )
                
        logger.debug("Received alarm account=%d user=%d eq=%d code=%d zone=%d part=%d"
                      %(account,user,eq,code,zone,part) )

        #TODO evil hack to fix IT100 API problems
        if ( part == 0 ):
            if ( zone != 0 ):
                part = 1
             
        name =  "alarm"+"-a"+str(account)
        if ( part != 0 ):
            name += "-p"+str(part)
        if ( zone != 0 ):
            name += "-z"+str(zone)

        crit = 5 
        value = 0
        if ( code > 0 ) and ( code < 300 ):
            crit = 4
            if eq == 3 :
                value = 0
            else:
                value = 1
        if ( code >= 300 ) and ( code < 400 ):
            crit =2
            if eq == 3:
                value = 0
            else:
                value = 0.75
        if ( code >= 400 ) and ( code < 500 ):
            crit = 3
            if eq == 3:
                value = user
            else:
                value = - user
        if ( code >= 500 ):
            crit = 5
            if eq == 3:
                value = 0
            else:
                value = 0.25

        addAlarmData( crit = crit, a=account, eq=eq, c=code, p=part, z=zone, u=user, note=note )

        if code == 302:
            name += "-battery"
        if code == 301:
            name += "-acPower"
        if code == 321:
            name += "-bell"
        if code == 351:
            name += "-phone"
        if code == 602:
            name += "-watchdog"

        if sensorExistsByName( name ):
            storeMeasurementByName( name,  value )
            addKnownIP( ip, name )
        else:
            logger.debug("Sensor to enroll %s at IP %s "%(name,ip) ) 
            info = findEnroll( name, ip )
    
    except apiproxy_errors.OverQuotaError, message:
        logger.error( "Out of quota to store data in postSensorValues: %s"%message)
        return HttpResponseNotFound( "<H1>Out of quota to store data in postSensorValues</H1>" )
         
    return HttpResponse() # return a 200 


def postSensorValues(request):
    enableQuota = False
    #enableQuota = True 

    ver = "TBD"
    try:
        ver = os.environ['SERVER_SOFTWARE']
    except:
        pass
    devel = ver.startswith("Development")
    if ( devel ): 
        enableQuota = False # disable quotas for development environment

    if request.method != 'POST':
        logger.debug( "Must use a POST to update values" )        
        return  HttpResponseNotFound( "<H1>Must use a POST to update values</H1>" )

    data = request.raw_post_data

    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2

    if ip == "173.181.12.124" : # Corin's IP
        logger.debug( "Black list Corin" )
        return HttpResponse(  "<H1>Too much data from you IP - call Fluffy</H1>" ) # return a 200 
        #return HttpResponseGone( "<H1>Too much data from you IP - call Fluffy</H1>" )
              
    token = 0
    if enableQuota:
        now = long( time.time() )

        minute = now - now % 60 # make window 1 minutes long 
        cacheKey = "key4-ipTokenBucketMinute:%s/%s"%(ip,minute)
        token = memcache.incr( cacheKey, 60 )

        rateLimit = 25 # Max number of request per minute from each IP address
        if enableQuota and token >= rateLimit:
            logger.debug( "IP %s exceed per minute rate limit"%ip )
            logger.debug( "data in post is %s "%data )
            if token == rateLimit:
                # should we log this or not
                logger.warning( "IP %s exceed per minute rate limit"%ip )
            logger.debug( "IP %s exceed per minute rate limit for sensor"%ip )     
            return HttpResponseForbidden( "<H1>User has exceed limit of %d requests per minute for sensor</H1>"%rateLimit )
        
    logger.debug("Got post of sensor values %s from %s count=%d"%(data,ip, token) )

    if enableQuota:
        addKnownIP( ip )
    
    try:
        jData = json.loads( data )
    except ValueError:
        logger.debug( "JSON data had error in parse")
        #return HttpResponse( content="<H1>JSON data had error in parse: %s </H1>"%e , mimetype=None,  status=400 )
        return HttpResponseNotFound( "<H1>JSON data had error in parse</H1><br /><pre>%s</pre>"%data )
    
    #try:
    if True:
        #TODO validate user input data here for security 
        logger.debug("j=%s"%str(jData) )

        logger.debug(" type is =%s"%str(type(jData)) )

        bt=0
        bn=str( "" )
        
        valArray = [];
        if ( type(jData) == list ):  # should depricate - this is the messurement object with no wrapper
            valArray = jData
        if ( type(jData) == dict ):
            valArray = jData['m']
            if jData.has_key('bt'):
                bt = long( jData['bt'] )
            if jData.has_key('bn'):
                bn = str( jData['bn'] )

        for m in valArray:
            name = bn + str( m['n'] )

            mTime = bt
            if m.has_key('t'):
                mTime = bt + long( m['t'] )

            value = None
            if m.has_key('v'):
                value = float( m['v'] )

            units = None
            if m.has_key('u'):
                units = str( m['u'] )
            
            sum = None
            if m.has_key('s'):
                sum = float( m['s'] )

            patchLevel = None
            if m.has_key('pl'):
                patchLevel = int( m['pl'] )

            energy = None  
            if m.has_key('j'):  # depricate 
                energy = float( m['j'] )

            if sensorExistsByName( name ):
                if enableQuota:
                    day = now - now % (24*3600) # make window 24 hours long  
                    cacheKey = "key4-sensorTokenBucketDay%s/%s"%(name,day)
                    token = memcache.incr( cacheKey, 24*3600 )
                    win = now - now % (60) # make window 1 min long  
                    cacheKey = "key4-sensorTokenBucketWindow%s/%s"%(name,win)
                    token = memcache.incr( cacheKey, 60 )

                    rateLimit = 10 # Max number of request per minute from each sensor
                    if enableQuota and token >= rateLimit:
                        logger.debug( "IP %s exceed per minute rate limit for sensors %s"%(ip,name) )
                        logger.debug( "post data is %s"%(data) )
                        if token == rateLimit:
                            # should we log this or not
                            logger.warning( "IP %s exceed per minute rate limit"%ip )
                        logger.debug( "IP %s exceed per minute rate limit for sensor %s "%(ip,name) )
                        return HttpResponseForbidden( "<H1>User has exceed limit of %d updates per minute for named sensor</H1>"%rateLimit )
    
                logger.info("Received measurment %s time=%d value=%s sum=%s units=%s energy=%s updateCount=%d"
                              %(name,mTime,value,sum,units,energy,token) ) 
                storeMeasurementByName( name, value, mTime=mTime, sum=sum, reset=False, energy=energy, patchLevel=patchLevel )
                
                if enableQuota:
                    addKnownIP( ip , name )
            else:
                logger.debug("Sensor to enroll %s at IP %s "%(name,ip) ) 
                info = findEnroll( name, ip )
       
        #sensorID= findSensorID( userName,sensorName, True ) #TODO - hack auto create new sensors 
        #if sensorID == 0 :
        #    return HttpResponseForbidden('<h1>Not a Valid sensor</h1>' )  
        #logger.debug( "Store user,sensor=%s,%s set to val=%s "%(userName,sensorName,data) )
        #storeMeasurement( sensorID,data)

    #except apiproxy_errors.OverQuotaError, message:
    #    logger.error( "Out of quota to store data in postSensorValues: %s"%message)
    #    return HttpResponseNotFound( "<H1>Out of quota to store data in postSensorValues</H1>" )
         
    return HttpResponse() # return a 200 



@login_required()
def jsonFour(request,user):
    assert 0
    # stuff for daily pie chart 
    tqxParams = request.GET.get('tqx','')
    logger.debug( "foo=%s", tqxParams )
    
    reqId = '0'
    try:
        params = dict( [part.split(':') for part in tqxParams.split(';') ] ) 
        reqId = params['reqId']
    except (ValueError,KeyError):
        pass

    html = ""
    html += "google.visualization.Query.setResponse({ \n"
    html += "version:'0.6',\n"
    # reqId:'0',status:'ok',sig:'6099996038638149313',
    html += "status:'ok', \n"

    html += "reqId:'%s', \n"%reqId

    html += "table:{ cols:[ {id:'Device',label:'Device',type:'string'}, \n"
    html += "               {id:'Value',label:'Value',type:'number'}], \n"
    html += "  rows:[ \n"

    query = StreamIDInfo.objects
    query = query.filter( user = user )
    results = query.all()[:1000] # TODO deal with more than 1000 
    
    for result in results:
        name = result.label
        units = result.units

        if units == '%':
            hydroUsage = 0.0
            try:
                hydroUsage = float(result.hydroUsage)
            except TypeError:
                pass
            
            elecUsage = 0.0
            try:
                elecUsage = float(result.elecUsage)
            except TypeError:
                pass
            
            gasUsage = 0.0
            try:
                gasUsage = float(result.gasUsage)
            except TypeError:
                pass
            
            v =  getDailyAverage(user,name,datetime.utcnow())
            kWh = v*24/1000 * ( elecUsage + gasUsage )
            try:
                sample = "   {c:[  {v:'%s'} , {v:%f}  ]}, \n"%( name , kWh )
                html += sample
            except ValueError:
                logger.debug( "Non numberic value in measurement value=%s"%( str(value) ) )

    html += "  ] } \n" #close rows, then table
    html += "} );\n" #close whole object 

    #response = HttpResponse("text/plain")
    response = HttpResponse()
    #response['Content-Disposition'] = 'attachment; filename=somefilename.csv'
    response.write( html );

    return response 


#@digestLogin(realm='fluffyhome.com')
@login_required()
def login(request,user=None):
    return HttpResponseRedirect("/user/%s/status/"%user)


#@digestLogin(realm='fluffyhome.com')
@login_required()
def enrollSensor2(request,sensorName,secret,user=None):
    return HttpResponseRedirect( "/user/%s/enroll/add/%s/"%(user,sensorName) )



##@digestLogin(realm='fluffyhome.com')
@login_required()
def pollWindAB1(request,loc,user=None):
    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2
   
    url = "http://www.ama.ab.ca/road_report/camera/%s.htm"%loc
    result = urlfetch.fetch(url, allow_truncated=True, follow_redirects=False, deadline=5, validate_certificate=False)

    html = "" 
    if result.status_code == 200:
        m = re.search('Air Temperature:\D*(?P<data>[\d.]*)',result.content)
        if m == None:
            logger.warning("Problem parsing out air temp from %s"%url )
        else:
            temp = m.group('data')
            html += "<p> temp = %s </p>"%temp

            name = 'alberta-%s-temp'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, temp )
            else:
                findEnroll( name, ip )

        m = re.search('Wind Speed:\D*(?P<data>[\d.]*)',result.content)
        if m == None:
            logger.warning("Problem parsing out wind speed from %s"%url )
        else:
            speed = m.group('data')
            html += "<p> speed = %s </p>"%speed

            name = 'alberta-%s-speed'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, speed )
            else:
                findEnroll( name, ip )

        m = re.search('at (?P<hour>\d{1,2}):(?P<min>\d\d)',result.content)
        if m == None:
            logger.warning("Problem parsing out update from %s"%url )
        else:
            time = int( m.group('hour') )%12  * 100 +  int( m.group('min') )
            html += "<p> time = %s </p>"%time

            name = 'alberta-%s-time'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, time )
            else:
                findEnroll( name, ip )

    else:
        html += "<p> Problem in fetch </p>"
        logger.warning( "Problem fetching content for %s - reponse code = %s "%(url,result.status_code) )
        
    response = HttpResponse()
    response.write( html );
    return response 


@login_required()
def pollWindAB2(request,loc,user=None):
    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2
   
    url = "http://www.ama.ab.ca/road_reports/cameras/%s"%loc
    result = urlfetch.fetch(url, allow_truncated=True, follow_redirects=False, deadline=5, validate_certificate=False)

    html = "" 
    if result.status_code == 200:
        m = re.search('Air Temperature:\D*(?P<data>[\d.]*)',result.content)
        if m == None:
            logger.warning("Problem parsing out air temp from %s"%url )
        else:
            temp = m.group('data')
            html += "<p> temp = %s </p>"%temp

            name = 'alberta-%s-temp'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, temp )
            else:
                findEnroll( name, ip )

        m = re.search('Wind Speed:\D*(?P<data>[\d.]*)',result.content)
        if m == None:
            logger.warning("Problem parsing out wind speed from %s"%url )
        else:
            speed = m.group('data')
            html += "<p> speed = %s </p>"%speed

            name = 'alberta-%s-speed'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, speed )
            else:
                findEnroll( name, ip )

        m = re.search('at (?P<hour>\d{1,2}):(?P<min>\d\d)',result.content)
        if m == None:
            logger.warning("Problem parsing out update from %s"%url )
        else:
            time = int( m.group('hour') )%12  * 100 +  int( m.group('min') )
            html += "<p> speed = %s </p>"%time

            name = 'alberta-%s-time'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, time )
            else:
                findEnroll( name, ip )

    else:
        html += "<p> Problem in fetch </p>"
        logger.warning( "Problem fetching content for %s - reponse code = %s "%(url,result.status_code) )
        
    response = HttpResponse()
    response.write( html );
    return response 


@login_required()
def pollWindAB3(request,loc,user=None):
    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2
   
    url = "http://www.weatherlink.com/user/%s/index.php?view=summary&headers=0"%loc
    result = urlfetch.fetch(url, allow_truncated=True, follow_redirects=False, deadline=5, validate_certificate=False)

    html = "" 
    if result.status_code == 200:
        m = re.search('Outside Temp</td>\s*.*>(?P<data>[\d.]{3,7}) C',result.content)
        if m == None:
            logger.warning("Problem parsing out air temp from %s"%url )
        else:
            temp = m.group('data')
            html += "<p> temp = %s </p>"%temp

            name = 'alberta-%s-temp'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, temp )
            else:
                findEnroll( name, ip )

        m = re.search('Wind Speed</td>\s*.*>(?P<data>[\d.]{1,3}) km/h',result.content)
        if m == None:
            logger.warning("Problem parsing out wind speed from %s"%url )
        else:
            speed = m.group('data')
            html += "<p> speed = %s </p>"%speed

            name = 'alberta-%s-speed'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, speed )
            else:
                findEnroll( name, ip )


        m = re.search('as of (?P<hour>\d{1,2}):(?P<min>\d\d)',result.content)
        if m == None:
            logger.warning("Problem parsing out update from %s"%url )
        else:
            time = int( m.group('hour') )%12  * 100 +  int( m.group('min') )
            html += "<p> time = %s </p>"%time

            name = 'alberta-%s-time'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, time )
            else:
                findEnroll( name, ip )

    else:
        html += "<p> Problem in fetch </p>"
        logger.warning( "Problem fetching content for %s - reponse code = %s "%(url,result.status_code) )
        
    response = HttpResponse()
    response.write( html );
    return response 


@login_required()
def pollWindAB4(request,loc,user=None):
    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2
   
    url = "http://text.www.weatheroffice.gc.ca/forecast/city_e.html?%s&unit=m"%loc
    result = urlfetch.fetch(url, allow_truncated=True, follow_redirects=False, deadline=5, validate_certificate=False)

    html = "" 
    if result.status_code == 200:
        m = re.search('Temperature:</dt><dd>(?P<data>[\d.]{1,5})&deg;C',result.content)
        if m == None:
            logger.warning("Problem parsing out air temp from %s"%url )
        else:
            temp = m.group('data')
            html += "<p> temp = %s </p>"%temp

            name = 'alberta-%s-temp'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, temp )
            else:
                findEnroll( name, ip )

        m = re.search('Wind Speed:</dt><dd>[NSWE]* (?P<data>[\d.]{1,5}) km/h',result.content)
        if m == None:
            logger.warning("Problem parsing out wind speed from %s"%url )
        else:
            speed = m.group('data')
            html += "<p> speed = %s </p>"%speed

            name = 'alberta-%s-speed'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, speed )
            else:
                findEnroll( name, ip )


        m = re.search('Observed at:[a-zA-Z'+"'"+' ]*(?P<hour>\d{1,2}):(?P<min>\d\d)',result.content)
        if m == None:
            logger.warning("Problem parsing out update from %s"%url )
        else:
            time = int( m.group('hour') )%12  * 100 +  int( m.group('min') )
            html += "<p> time = %s </p>"%time

            name = 'alberta-%s-time'%loc
            if sensorExistsByName( name ):
                storeMeasurementByName( name, time )
            else:
                findEnroll( name, ip )

    else:
        html += "<p> Problem in fetch </p>"
        logger.warning( "Problem fetching content for %s - reponse code = %s "%(url,result.status_code) )
        
    response = HttpResponse()
    response.write( html );
    return response 
