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
from django.shortcuts import render_to_response
from google.appengine.ext.db import djangoforms
#from django import newforms as forms
#from django.newforms import form_for_model,form_for_instance
from django import forms
from django import VERSION as DJANGO_VERSION
from django.utils import simplejson as json  # fix when we can use Python 2.6 to just be import json 

from google.appengine.api.labs import taskqueue
from google.appengine.ext import db
from google.appengine.runtime import apiproxy_errors

from google.appengine.api import mail

from google.appengine.api import urlfetch

from djangohttpdigest.decorators import digestProtect,digestLogin

from store.models import *

# TODO - need to uncomment these and install on notebook comp 
#import oauth2 as oauth
#from oauthtwitter import OAuthApi


def twitterCallback(request):
    token = request.GET.get('oauth_token',None)
    verifier = request.GET.get('oauth_verifier',None)

    assert token, "Twitter callback URL did not contain a oauth token"
    assert verifier,  "Twitter callback URL did not contain a oauth token"

    logging.info( "Twitter temp token in callback param is " + token )
 
    # find the user with that token
    query = User.all()
    query.filter( 'twitterTempToken =', token )
    user = query.get()
    assert( user )
     
    return HttpResponseRedirect( '/user/' + user.userName + '/twitterVerify?tok=' + token + '&verify=' + verifier )


#@digestProtect(realm='fluffyhome.com') 
def twitterVerify(request,userName):
    token = request.GET.get('tok',None)
    verifier = request.GET.get('verify',None)

    assert token, "Twitter callback URL did not contain a oauth token"
    assert verifier,  "Twitter callback URL did not contain a oauth token"
  
    # get the temp credential
    query = User.all()
    query.filter( 'userName =', userName )
    user = query.get()
    assert( user )

    assert user.twitterTempToken == token
    
    tempToken = {}
    tempToken['oauth_token'] = user.twitterTempToken
    tempToken['oauth_token_secret'] = user.twitterTempSecret

    logging.info( "Twitter temp token in verify is " + user.twitterTempToken )
 
    query = SystemData.all()
    sys = query.get()
    assert( sys )
    assert( sys.twitterConsumerToken )
    
    twitter = OAuthApi( sys.twitterConsumerToken, sys.twitterConsumerSecret )

    accessToken = twitter.getAccessToken( tempToken, verifier )

    try:
        user.twitterAccessToken  = accessToken['oauth_token']
        user.twitterAccessSecret = accessToken['oauth_token_secret']
        user.put()
    except:
        # don't have a valid access token
        logging.info( "Did not get twitter access token"  )

    return HttpResponseRedirect( '/user/' + userName + '/prefs/' )
    

@digestProtect(realm='fluffyhome.com') 
def twitterLogout(request,userName):
    # remove the twitter credentials
    query = User.all()
    query.filter( 'userName =', userName )
    user = query.get()
    assert( user )
    user.twitterTempToken = ''
    user.twitterTempSecret = ''
    user.twitterAccessToken = ''
    user.twitterAccessSecret = ''
    user.put()
    return HttpResponseRedirect( '/user/' + userName + '/prefs/' )


@digestProtect(realm='fluffyhome.com')  
def twitterLogin(request,userName):
    query = SystemData.all()
    sys = query.get()
    assert( sys )
    assert( sys.twitterConsumerToken )
    
    twitter = OAuthApi( sys.twitterConsumerToken,  sys.twitterConsumerSecret )

    tempToken = twitter.getRequestToken()
    assert( tempToken)
    
    # save the temp credential
    query = User.all()
    query.filter( 'userName =', userName )
    user = query.get()
    assert( user )
    user.twitterTempToken = tempToken['oauth_token']
    user.twitterTempSecret = tempToken['oauth_token_secret']
    user.twitterAccessToken = ''
    user.twitterAccessSecret = ''
    user.put()

    logging.info( "Twitter temp token in login is " + user.twitterTempToken )
    
    authURL = twitter.getAuthorizationURL( tempToken )
    assert( authURL )

    return HttpResponseRedirect( authURL )
   
    
@digestProtect(realm='fluffyhome.com') 
def test1User(request,userName):
    #query = SystemData.all()
    #sys = query.get()
    #if  sys.twitterConsumerToken== None:
    #    sys.twitterConsumerToken = ""
    #    sys.twitterConsumerSecret = ""
    #    sys.put()
    #
    #query = User.all()
    #query.filter( 'userName =', userName )
    #user = query.get()
    #if user.twitterAccessToken == None:
    #    user.twitterAccessToken  = ""
    #    user.twitterAccessSecret  = ""
    #    user.put()
    
    form = []
    msg = "my message"
    
    consumer_key = ""
    consumer_secret = ""

    access_tok = ""
    access_tok_secret = ""

    #twitter = OAuthApi(consumer_key, consumer_secret, access_tok, access_tok_secret)
    #res = twitter.VerifyCredentials()
    #msg = res['status']['text']
    
    return render_to_response('userPrefs.html', { 'msg':msg, 
                                                  'form':form,
                                                  'user':userName, 
                                                  'host' : request.META["HTTP_HOST"] } )


    
    
def editUser( request, userName ):
    record = findUserByName( userName )
    
    if record is not None:
        return HttpResponse("<h1>User %s already exists</h1>"%(userName) )

    password = "123456" # TODO fix to use random 
    createUser( userName , password  ) 
    return HttpResponse("<h1>Created user: %s with password %s </h1>"%(userName,password) )
 

class EditUserForm(djangoforms.ModelForm):
    class Meta:
        model = User
        exclude = [ 'userName','passwd','active','userID','settingEpoch' ]
    def __init__(self, *args, **kwargs):
        super(djangoforms.ModelForm, self).__init__(*args, **kwargs)



@digestProtect(realm='fluffyhome.com') # TODO get from settings file 
def userPrefs( request, userName ):
    msg = "Edit any values you wish to change above then press Update"

    record = findUserByName( userName )
    assert record is not None, "can't find record in DB"

    if request.method == 'POST': 
        form = EditUserForm(request.POST, instance=record)
        if form.is_valid():
            logging.info( "input form IS valid" )

            #logging.info( "form extra group = %s", form.cleaned_data['extraGroup'] )

            info = form.save(commit=False)
        
            #logging.info( "form extra group = %s", info.extraGroup )
            logging.info( "done" )
            
            msg ="Data succesfully saved"

            if ( record.newPwd is not None ) and ( record.newPwd is not "" ) :
                if record.newPwd == record.newPwdAgain :
                    record.passwd = record.newPwd
                    msg ="Password succesfully changed"
                    record.newPwd = ""
                    record.newPwdAgain = ""
                else:
                    msg ="New passwords did not match and password was not changed"

            record.put()
            updateUserSettingsEpoch(userName)
        else:
            logging.error( "Error in form data to edit sensor form=%s"%( str( form )) )
            msg = "Some problem processing form"
            
    else:
        form = EditUserForm( instance=record ,  auto_id=False  )

    twitterEnabled = False
    if record.twitterAccessToken:
        if record.twitterAccessToken != '':
            twitterEnabled = True
        
    logging.info( "debug for form=%s"%form )
    return render_to_response('userPrefs.html', { 'msg':msg, 
                                                  'form':form,
                                                  'user':userName,
                                                  'twitterEnabled':twitterEnabled,
                                                  'host' : request.META["HTTP_HOST"] } )



#@digestProtect(realm='fluffyhome.com') # TODO get from settings file 
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
        cacheKey = "key2-sensorTokenBucketDay%s/%s"%( s['name'], day )
        updates = memcache.get( cacheKey )
        if updates != None:
            s['updatesDay'] = int(updates)
        else:
            s['updatesDay'] = int(0)

        cacheKey = "key2-sensorTokenBucketWindow%s/%s"%(s['name'],minute1)
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
        cacheKey = "key2-ipTokenBucketMinute:%s/%s"%(ip,minute0)
        updates0 = memcache.get( cacheKey )
        if updates0 == None:
            updates0 = 0
        updates0 = int( updates0 )

        cacheKey = "key2-ipTokenBucketMinute:%s/%s"%(ip,minute1)
        updates1 = memcache.get( cacheKey )
        if updates1 == None:
            updates1 = 0
        updates1 = int( updates1 )
        
        ips.append( { 'ip':ip , 'updates0':updates0 , 'updates1':updates1 } )
        
    return render_to_response( template , { 'sensors':sensors,'ipAddrs':ips,
                                            'host':request.META["HTTP_HOST"] }) 



@digestProtect(realm='fluffyhome.com') # TODO get from settings file 
def showGraphs( request, userName ):
    template = "showGraphs.html"
    
    sensors = findAllResourceSensors( findUserIDByName( userName ) )

    sensors = sorted( sensors , cmp=lambda x,y: cmp( x['label'], y['label'] ) )

    return render_to_response( template , { 'user':userName,
                                            'sensors':sensors,
                                            'host':request.META["HTTP_HOST"] }) 


def upgradeHourly(request):
    val = hourlyUpgrade()
    return HttpResponse("<h1>Upgraded all Hourly = %s</h1>"%val)


@digestProtect(realm='fluffyhome.com') 
def resetSensors(request,userName):
    # reset all values, integrals, and energy readings for all the users sensor
    
    sensorsIDs = findAllSensorIdNamePairs( findUserIDByName( userName ) )
    for sensorData in sensorsIDs:
        sensorID = sensorData[0]
        storeMeasurement( sensorID , value=0.0 , reset=True )

    return HttpResponse("<h1>Reset all sensors</h1>")


@digestProtect(realm='fluffyhome.com') 
def showPlotOLD_NO_USE(request,userName,sensorName):
    sensorID = findSensorID(userName,sensorName)
    if sensorID == 0 :
        return HttpResponseNotFound('<h1>For user=userName=%s sensor=%s not found</h1>'%(userName,sensorName) )  

    data = { 'sensorName': sensorName ,
             'user':userName,
             'label': getSensorLabelByID(sensorID),
             'host' : request.META["HTTP_HOST"] }
    return render_to_response('showPlot.html', data )


@digestProtect(realm='fluffyhome.com') 
def showLineGraph(request,userName,sensorName):
    sensorID = findSensorID(userName,sensorName)
    if sensorID == 0 :
        return HttpResponseNotFound('<h1>For user=userName=%s sensor=%s not found</h1>'%(userName,sensorName) )  

    data = { 'sensorName': sensorName ,
             'user':userName,
             'label': getSensorLabelByID(sensorID),
             'host' : request.META["HTTP_HOST"] }
    return render_to_response('lineGraph.html', data )


#@digestProtect(realm='fluffyhome.com')  # todo - fix this security nightmare 
def showLineGraphCSV(request,userName,sensorName):
    sensorID = findSensorID( userName, sensorName )
    if sensorID == None:
        return HttpResponseNotFound('<h1>user=%s stream name=%s not found</h1>'%(user,streamName) )  

    html = ""

    #  get users time zone from DB
    userID =  findUserIdByName( userName )
    assert userID > 0 
    userMeta = getUserMetaByUserID( userID )
    timeOffset = userMeta['timeZoneOffset']
    assert timeOffset != None

    # get most recent values
    query = Measurement2.all()
    query.filter( 'sensorID =', sensorID )
    query.order("-time") #TODO - should have time based limits 
    measurements = query.fetch(900) #TODO need to deal with more than 1000 meassurements

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
            logging.debug( "Non numberic value in measurement value=%s"%( str(value) ) )

    #response = HttpResponse("text/plain")
    response = HttpResponse()
    #response['Content-Disposition'] = 'attachment; filename=somefilename.csv'
    response.write( html );
    return response 


#@digestProtect(realm='fluffyhome.com')  # todo - fix this security nightmare 
def showPlotJson_OLD_NO_USE(request,userName,sensorName):
    sensorID = findSensorID( userName, sensorName )
    if sensorID == None:
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
    query = Measurement2.all()
    query.filter( 'sensorID =', sensorID )
    query.order("-time") #TODO - should have time based limits 
    measurements = query.fetch(900) #TODO need to deal with more than 1000 meassurements

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
            logging.debug( "Non numberic value in measurement value=%s"%( str(value) ) )

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


#@digestProtect(realm='fluffyhome.com') # todo fix 
def usageJson(request,userName,sensorName,type,period):
    tqxParams = request.GET.get('tqx','')
    
    reqId = '0'
    try:
        params = dict( [part.split(':') for part in tqxParams.split(';') ] ) 
        reqId = params['reqId']
    except (ValueError,KeyError):
        pass

    logging.debug("usageJson reqId = %s"%reqId)

    now = long( time.time() )
    now = now - now%3600

    epoch = getUserSettingEpoch( userName )

    head = ""
    head += "google.visualization.Query.setResponse({ \n"
    head += "version:'0.6',\n"
    head += "status:'ok', \n"
    head += "reqId:'%s', \n"%reqId

    cacheKey = "key2-usageJson:%d/%s/%s/%s/%s/%d"%(epoch,userName,sensorName,type,period,now)
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

    if period == "day": 
        mid = now 
        start = mid - 24*3600
        end = mid 
        step = 3600
        hour = None

    if period == "0day": 
        mid = now - ( (now + timeOffsetSeconds )%(24*3600) ) # todo deal with  and 4 am is new midnight
        start = mid 
        end = mid  + 24*3600
        step = 3600
        hour = None

    if period == "1day": 
        mid = now - ( (now + timeOffsetSeconds )%(24*3600) ) # todo deal with  and 4 am is new midnight
        start = mid - 24*3600
        end = mid 
        step = 3600
        hour = None

    if period == "2day" :
        mid = now - ( (now + timeOffsetSeconds )%(24*3600) ) # todo deal with  and 4 am is new midnight
        start = mid - 24*3600
        end = mid  + 24*3600
        step = 3600 
        hour = None

    if period == "7day":
        mid = now - ( (now + timeOffsetSeconds )%(24*3600) ) # todo deal with  and 4 am is new midnight
        start = mid - 7*24*3600
        end = mid
        step = 3600 * 24 
        hour = (start/3600) % 24

    if period == "30day":
        mid = now - ( (now  + timeOffsetSeconds )%(24*3600) ) # todo deal with  and 4 am is new midnight
        start = mid - 30*24*3600
        end = mid
        step = 3600 * 24 
        hour = (start/3600) % 24

    userID =  findUserIdByName( userName )
    assert userID > 0 

    #  get all costs from DB
    userMeta = getUserMetaByUserID( userID )

    # get all the hourly values from the database
    values = getHourlyByUserIDTime( userID, start, end , hour )

    for t in range( start , end, step ):
        ret += "   {c:[  \n"

        localTime = datetime.fromtimestamp( t ) + timedelta( hours=timeOffset ) 
        if ( step == 3600 ):
            ret += "        {v:'%02d:00'}, \n"%( localTime.hour ) 
        elif ( step == 24*3600 ):
            ret += "        {v:'%s'}, \n"%(  localTime.strftime("%a") )
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
                    start = value.joules
                    startI = value.integral

            value = findValueByTimeSensorID( values , t+step , sensorID )
            if value is not None:
                if sensor['group'] is True:
                    end = value.groupOtherEnergy 
                else:
                    end = value.joules
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

    memcache.set( cacheKey, ret , 4*3600 )

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
            logging.debug( "Non numberic value in measurement value=%s"%( str(value) ) )

    html += "  ] } \n" #close rows, then table
    html += "} );\n" #close whole object 
    return html


#@digestProtect(realm='fluffyhome.com') # todo fix 
def todayJson(request,userName,sensorName):
    sensorID = findSensorID(userName,sensorName)
    if sensorID == 0 :
        return HttpResponseNotFound('<h1>userName=%s stream name=%s not found</h1>'%(userName,sensorName) )  

    tqxParams = request.GET.get('tqx','')
    logging.info( "foo=%s", tqxParams )
    
    #  get users time zone from DB
    userID =  findUserIdByName( userName )
    assert userID > 0 
    userMeta = getUserMetaByUserID( userID )
    timeOffset = userMeta['timeZoneOffset']
    assert timeOffset != None

    #vals = getDayValues( userName,sensorName, datetime.utcnow() )
    sensorID = findSensorID( userName,sensorName )
    assert sensorID > 0 # todo should html erro 

    utime = long( time.time() )
    utime = utime - utime % 3600 # get prev hour time 
    vals = []
    for i in range(-24,0):
        #ptime = datetime.utcnow() + timedelta( hours=i )
        #startTime = datetime( ptime.year, ptime.month, ptime.day, ptime.hour )
        #timeTuple = startTime.timetuple()
        #floatTime =  time.mktime( timeTuple )
        #utime = long( floatTime )

        t = utime + i*3600 # is is negative so add it 
        dTime = datetime.fromtimestamp( t )

        v = 0
        start = getHourlyIntegralBySensorID( sensorID, t)
        end   = getHourlyIntegralBySensorID( sensorID ,t+3600)
        if ( start is not None ) and ( end is not None ):
            if ( end >= start ) and ( start >= 0 ):
                v = (end-start)/3600.0
        logging.debug("sensor=%s hour=%d start=%s end=%s i=%s v=%s"%( getSensorLabelByID(sensorID),
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
        return HttpResponseNotFound('<h1>userName=%s sensor name=%s not found</h1>'%(userName,sensorName) )

    data = { 'sensorName': sensorName ,
             'user': None,
             'graphUser':userName,
             'label': getSensorLabelByID(sensorID),
             'host' : request.META["HTTP_HOST"] }
    return render_to_response('graphTodaySmall.html', data )


@digestProtect(realm='fluffyhome.com') 
def graphToday(request,userName,sensorName):
    sensorID = findSensorID( userName, sensorName )
    if sensorID == 0 :
        return HttpResponseNotFound('<h1>userName=%s sensor name=%s not found</h1>'%(userName,sensorName) )

    data = { 'sensorName': sensorName ,
             'user': userName,
             'graphUser':userName,
             'label': getSensorLabelByID(sensorID),
             'host' : request.META["HTTP_HOST"] }
    return render_to_response('graphToday.html', data )


@digestProtect(realm='fluffyhome.com') 
def dumpUser(request,userName):
    response = HttpResponse(mimetype='application/xml')
    response['Content-Disposition'] = 'attachment; filename=%s-dump.xml'%userName

    response.write( "<dump>\n" )

    user = findUserByName( userName ) 
    response.write( "<user userID='%d' userName='%s' \n"%( user.userID, user.userName, ) )
    response.write( "   email='%s' "%( user.email ) )
    response.write( "   email2='%s' "%( user.email2 ) )
    response.write( "   email3='%s' "%( user.email3 ) )
    response.write( "   sms1='%s' "%( user.sms1 ) )
    response.write( "   timeZoneOffset='%f' "%( user.timeZoneOffset ) )
    response.write( "   midnightIs4Am='%d' "%( user.midnightIs4Am ) )
    response.write( "   gasCost='%f' "%( user.gasCost ) )
    response.write( "   elecCost='%f' "%( user.elecCost ) )
    response.write( "   waterCost='%f' "%( user.waterCost ) )
    response.write( "   gasCO2='%f' "%( user.gasCO2 ) )
    response.write( "   elecCO2='%f' >\n"%( user.elecCO2 ) )

    #d = user.to_xml()  # This includes the users password 
    #response.write( d )
    response.write( "</user>\n" )

    sensors = findAllSensorsByUserID( findUserIdByName( userName ) )
    for sensor in sensors:
        if sensor.groupTotal is None: 
            sensor.groupTotal=False
        if sensor.ignore is None: 
            sensor.ignore=False

        attr = ""
        attr += " sensorID='%d'"%sensor.sensorID 
        attr += " sensorName='%s'"%sensor.sensorName 
        attr += " label='%s'"%sensor.label 
        attr += " userID='%d'"%sensor.userID 
        attr += " apiKey='%s'"%sensor.apiKey 

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
            attr += " maxUpdateTime='%d'"%sensor.maxUpdateTime 

        response.write( "<sensor %s >\n"%attr )
        d = sensor.to_xml()
        response.write( d )
        response.write( "</sensor>\n" )
             
        measurements = findRecentMeasurements( sensor.sensorID )
        for m in measurements:
            if m.integral == None:
                m.integral = 0.0
            if m.joules == None:
                m.joules = 0.0
            md="<measurement user='%s' sensor='%s' time='%d' value='%f' integral='%f' joules='%f' />\n"%(
                userName, sensor.sensorName, 
                m.time, m.value,
                m.integral, m.joules )
            response.write( md )

    if ( userName == 'fluffy' ):
        alarms = findRecentAlarmData( 3261 ) # TODO , don't hard code alarm ID for user 
        for a in alarms:
            ad="<alarm time='%d' id='%d' eq='%d' code='%d' part='%d' crit='%d't zone='%d' user='%d' note='%s' />\n"%(
                a.time,a.alarmID, a.eq, a.code, a.part, a.crit, a.zone, a.users, a.note )
            response.write( md )
        
    response.write( "</dump>\n" )

    return response


class EditSensorForm(djangoforms.ModelForm):
    #inGroup = forms.TypedChoiceField(  coerce=int )
    inGroup2 = forms.TypedChoiceField(  coerce=int )
    class Meta:
        model = Sensor
        exclude = [ 'sensorID','userID','sensorName','inGroup','apiKey','tags','watts','public','killed','displayMin','displayMax' ]
    def __init__(self, *args, **kwargs):
        super(djangoforms.ModelForm, self).__init__(*args, **kwargs)
        self.fields['inGroup2'].choices = findAllGroupsIdNamePairs( kwargs['instance'].userID )


        

@digestProtect(realm='fluffyhome.com') 
def editSensor(request,userName,sensorName):
    sensorID = findSensorID(userName,sensorName)
    if sensorID == 0 :
        return HttpResponseNotFound('<h1>userName=%s stream name=%s not found</h1>'%(userName,sensorName) )
    
    record = findSensor( sensorID ,"editSensor")
    assert record is not None, "can't find record in DB"

    sensorData = { 'user': userName , 'streamName': sensorName , 'category':record.category }
    msg = "Edit any values you wish to change above then press Update"

    if request.method == 'POST': 
        form = EditSensorForm(request.POST, instance=record)
        if form.is_valid():
            logging.info( "input form IS valid" )
            info = form.save(commit=False)

            x = form.clean()
            group =  x['inGroup2']
            #logging.info( "inGroup2 = %s"%( group ))
            record.inGroup = group
            
            if record.sensorName == "All":
                record.inGroup = 0

            record.put()
            updateUserSettingsEpoch(userName)
            msg ="Data succesfully saved"
        else:
            logging.error( "Error in form data to edit sensor form=%s"%( str( form )) )
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

    #logging.info( "debug for form=%s"%form )
    return render_to_response('editSensor.html', { 'msg':msg, 
                                             'form':form,
                                             'sensor': sensorData,
                                             'user':userName, 
                                             'host' : request.META["HTTP_HOST"] } )


@digestProtect(realm='fluffyhome.com') 
def createSensor(request,userName,sensorName):

    userID = findUserIDByName( userName  )
    assert userID > 0

    sensorID = findSensorID(userName,sensorName,create=True)
    assert sensorID > 0

    record = findSensor( sensorID ,"createSensor" )
    assert record is not None, "can't find record in DB"

    if request.method == 'POST': 
        #logging.debug( "POST data is %s"%str(request.POST) ) 
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

        record.put()
        updateUserSettingsEpoch(userName)
            
        return HttpResponse('<h1>Updated sensor %s</h1>'%sensorName  )  

    return HttpResponseNotFound('<h1>Problem with create sensor</h1>%s'%( sensorName ) )



def loadAllSensors(request,userName):
    # check user exists 
    if findUserIdByName(userName) == 0 :
        return HttpResponseNotFound('<h1>Error: No user with name %s</h1>'%(userName) )  

    sensorsIDs = findAllSensorsIDsByUserID( findUserIdByName( userName ) )

    for s in sensorsIDs:
        assert s > 0
        meta = findSensorMetaByID( s ,"showAllSensors" );

    return HttpResponse('<h1>Updated sensor cache for user %s</h1>'%(userName) )  


def showAllWindSensors(request):
    # check user exists
    userName = 'wind'
    if findUserIdByName(userName) == 0 :
        return HttpResponseNotFound('<h1>Error: No user with name %s</h1>'%(userName) )  

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
            logging.warning( "Moved sensor %s to All group"%meta['sensorName'] )

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

@digestProtect(realm='fluffyhome.com') 
def showAllSensors(request,userName):
    return showAllSensorsFunc(request,userName=userName)


def showAllSensorsFunc(request,userName):
    # check user exists 
    if findUserIdByName(userName) == 0 :
        return HttpResponseNotFound('<h1>Error: No user with name %s</h1>'%(userName) )  

    sensorDataList = []

    allGroupSensorID = findSensorID(userName,"All",create=True)
    assert allGroupSensorID > 0, "There is no group named 'All' for user %s"%userName

    sensorsIDs = findAllSensorsIDsByUserID( findUserIdByName( userName ) )
    
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
            logging.warning( "Moved sensor %s to All group"%meta['sensorName'] )

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
            sum = findGroupPower( sensorID , None, Set() ) 
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
                        sensorData['joules'] = e / (3600.0 * 1000.0) # convert J to kWH
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



@digestProtect(realm='fluffyhome.com') 
def usage(request,userName):
    #todo erro bad user 

    # check user exists 
    userID = findUserIdByName(userName)
    if userID == 0 :
        return HttpResponseNotFound('<h1>Error: No user with name %s</h1>'%(userName) )  

    # todo , add proper checks for user/sensor exists for all pages 

    #  get all costs from DB
    userMeta = getUserMetaByUserID( userID )

    # todo - rounding for display is lame and sort of wrong 

    sensorID =  findSensorID( userName, "All")
    assert sensorID != 0, "Group 'All' does not exist for user %s"%userName

    hydro =findSensorWater( sensorID , "Water" ) #  this is in l/s
    elec = findSensorPower( sensorID, "Electricity" )
    gas =  findSensorPower( sensorID , "Gas" )

    vars = {}
    vars['host'] = request.META["HTTP_HOST"]
    vars['user'] = userName

    #todo move water to hydro 

    vars['waterCostPh'] = hydro*3600 * userMeta['waterCost'] 

    vars['gaskW']  = int(gas)/1000.0 #todo fix round
    vars['gasCostPh'] = gas/1000 * userMeta['gasCost'] 
    vars['gasC02kgph'] = gas/1000 * userMeta['gasCO2']

    vars['eleckW'] = int(elec)/1000.0  #todo fix round
    vars['elecCostPh'] = elec/1000 * userMeta['elecCost']
    vars['eleckC02kgph'] = elec/1000 * userMeta['elecCO2']

    vars['hydroLpm'] = hydro*60

    vars['totCostPh'] = vars['gasCostPh'] + vars['elecCostPh'] + vars['waterCostPh']
    vars['totC02kgph'] = vars['gasC02kgph'] + vars['eleckC02kgph']

    # round for display 
    vars['totCostPh'] = int(  vars['totCostPh'] *100 ) / 100.0
    vars['totC02kgph'] =  int( vars['totC02kgph'] * 1000 ) / 1000.0

    return render_to_response('usage.html', vars )


class AddGroupForm(djangoforms.ModelForm):
    name = forms.RegexField( "^\w[\-\w]{0,64}$" ) 

@digestProtect(realm='fluffyhome.com') 
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
            logging.info( "input form is valid" )

            x = form.clean()
            name = x['name']
            
            logging.info( "add new group name = %s", name )
            msg = "Created new %s group"%name 
            updateUserSettingsEpoch(userName)

            sensorName = name 
            findSensorID( userName, sensorName, create=True , createGroup=True )
    
            return HttpResponseRedirect( "/sensor/%s/%s/meta/"%(userName,sensorName) )

        else:
            logging.error( "Error in the create group Name of '%s'"%( str( form )) )
            msg = "Group Name must only have alphanumeric, underscore, or dash and start with alphanumeric character"
            
    else:
        form = AddGroupForm()

    return render_to_response('enroll.html', { 'sensors':sensors,
                                               'user':userName,
                                               'msg':msg, 
                                               'form':form,
                                               'host' : request.META["HTTP_HOST"] } )
    


@digestProtect(realm='fluffyhome.com') 
def addSensor(request,userName,sensorName):
    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2
    secret = "secretTODO"

    enrollSensor( ip, sensorName, userName, secret )
    findSensorID( userName, sensorName, create=True ) # todo - rethink security of who gets to claim a sensor and when

    return HttpResponseRedirect( "/sensor/%s/%s/meta/"%(userName,sensorName) )




#######OLD OLLD OLD OLD OLD #######################################################################

def totalElec(request,user):
    assert 0
    usage = getCurrentUsage( user )

    vars = {}
    vars['host'] = request.META["HTTP_HOST"]
    vars['user'] = user

    vars['eleckW'] = usage['elecUsage']/1000

    return render_to_response('totalElec.html', vars )


def enrollOld(request,streamName):
    assert 0
    host = request.META["HTTP_HOST"]
    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2

    info = findEnroll( streamName, ip )

    if info.user == "":
        return HttpResponseNotFound('<p> Waiting for user to claim stream </p>' )

    url = "http://%s/sensor/%s/%s/value/"%(host,info.user,info.sensorName)
    data = "%s\n"%info.user # if we had DNS on sensors, might be better to return a URL 
    data += "%s\n"%info.secret
    data += "%s\n"%url

    return HttpResponse( data )


def taskUpdateValues(userName,sensorName,t):
    logging.debug("In taskUpdateValues user=%s sensor=%s t=%s"%(userName,sensorName,t) )
    
    sensorID = getSensorIDByName( sensorName ) # todo - should check userName too
    assert sensorID > 0

    assert t is not None
    assert t > 0

    t = t - t % 3600
    getHourlyEnergyBySensorID( sensorID , t )

                  
def qTaskUpdate(userName,sensorName,t):
    logging.info("qTaskUpdate: user=%s sensor=%s time=%s"%(userName,sensorName,t) )
 
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


def updateValues(request,userName,sensorName,pTime):
    logging.info("TASK: Running task updateValues %s/%s/%s"%(userName,sensorName,pTime) )

    #if userName != "*" and sensorName != "*":
    #    if not streamExists(userName,sensorName) : # todo fix 
    #        return HttpResponseNotFound('<h1>user=%s sensor name=%s not found</h1>'%(userName,sensorName) )
     
    qTaskUpdate( userName, sensorName, pTime )

    logging.info("TASK: completed task updateValues %s/%s/%s"%(userName,sensorName,pTime) )
    return HttpResponse('<h1>Queued tasks to updated Values</h1>'  )  


def updateNotify(request,userName,sensorName):
    logging.info("TASK: Running task updateNotify %s %s"%(userName,sensorName,) )

    # TODO
    if userName == "*" :
        users = findAllUserNames()
    else:
        users = [ userName ]
    for userName in users:
        if sensorName == "*":
            sensors = findAllSensorsByUserID( findUserIDByName( userName ) )
        else:
            sensors = [ findSensor( getSensorIDByName( sensorName ) ) ]
        for sensor in sensors: # do ones that a NOT a group
            if sensor.killed != True:
                if sensor.category != "Group":
                    checkNotify(userName, sensor.sensorName )

    logging.info("TASK: completed task updateNotify %s %s"%(userName,sensorName) )
    return HttpResponse('<h1>Completed tasks to updated Value</h1>'  )  


def checkNotify(userName, sensorName):
    logging.debug( "CheckNotify %s %s "%(  userName, sensorName  ) )

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
                logging.debug( "Sensor just went frozen %s %s "%(  userName, meta['sensorName']  ) )
                sendNotify(userName,  meta['sensorName'],
                           "Sensor %s is frozen"%( meta['label'] ), 
                           "Sensor %s stoped reporting %s minutes ago"%( meta['label'], (now-lastTime)/60.0 )
                           )


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
        logging.debug( "Sent email To:%s Subject:%s Body:%s"%(  userMeta['email1'], summary, note ) )


                
def updateAllValues(request):
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
                        logging.debug( "Updated %s/%s/%d"%(  userName, sensor.sensorName , (t-now)/3600 ) )
            for sensor in sensors: # do the ones that ARE a group
                if sensor.killed != True:
                    if sensor.category == "Group":
                        taskUpdateValues( userName, sensor.sensorName , t )
                        logging.debug( "Updated %s/%s/%d"%(  userName, sensor.sensorName , (t-now)/3600 ) )

    return HttpResponse('<h1>Completed update all hourly values</h1>'  )  


def updateAllValuesNow(request):
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
                        logging.debug( "Updated %s/%s/%d"%(  userName, sensor.sensorName , (t-now)/3600 ) )
            for sensor in sensors:  # do the ones that ARE a group
                if sensor.killed != True:
                    if sensor.category == "Group":
                        qTaskUpdate( userName, sensor.sensorName , t )
                        logging.debug( "Updated %s/%s/%d"%(  userName, sensor.sensorName , (t-now)/3600 ) )

    return HttpResponse('<h1>Completed update all hourly values</h1>'  )  



def pipes(request,user):
    assert 0 
    pipeList = []

    query = StreamIDInfo.all()
    query.filter( 'user =', user )
    results = query.fetch(1000)

    getAllStreamNames( user )

    for result in results:
        pipe = {}
        pipe['user'] = result.user
        pipe['name'] = result.streamName
        pipe['label'] = result.label
        pipe['units'] = result.units
       
        try:
            key = result.streamID.key()
        except AttributeError:
            logging.info( "found bad StreamID in database %s"%( str(pipe) )  )
            continue
        
        # get most recent value 
        query = Measurement.all()
        query.filter( 'streamID =', key )
        query.order("-time")
        measurement = query.get()

        if measurement == None:
            logging.info( "No measurement record in DB for %s"%( str(pipe) )  )
        else:
            pipe['time'] = measurement.time
            pipe['value'] = measurement.value

        pipeList.append( pipe )

    return render_to_response('feeds.html', { 'user':user, 'pipeList': pipeList , 'host':request.META["HTTP_HOST"] })


def about(request):
    ver = os.environ['SERVER_SOFTWARE']
    devel = ver.startswith("Development")
   
    return render_to_response('about.html' , { 
        'djangoVersion': "%s.%s.%s"%( DJANGO_VERSION[0],  DJANGO_VERSION[1], DJANGO_VERSION[2] ) ,
        'pythonVersion': "%s"%( sys.version ) ,
        'osVersion': "%s"%( ver ) ,
        'host':request.META["HTTP_HOST"] } )


@digestProtect(realm='fluffyhome.com')  # old - should depricate 
def store(request,userName,sensorName):
    return storeNoAuth(request,userName,sensorName) 


def storeNoAuth(request,userName,sensorName): #old - should depricate 
    if request.method != 'PUT':
        return HttpResponseForbidden('<h1>Must use method PUT</h1>' )  

    data = request.raw_post_data
    #TODO validate user input data here for security 
    
    sensorID = findSensorID( userName,sensorName )
    if sensorID == 0 :
        return HttpResponseForbidden('<h1>Not a Valid sensor</h1>' )  

    logging.debug( "Store user,sensor=%s,%s set to val=%s ip=%s "%(userName,sensorName,data,ip) )
    storeMeasurement( sensorID,data)
    return HttpResponse() # return a 200 


def postAlarmValues(request):
    enableQuota = True 

    ver = os.environ['SERVER_SOFTWARE']
    devel = ver.startswith("Development")
    if ( devel ): 
        enableQuota = False # disable quotas for development environment

    if request.method != 'POST':
        return  HttpResponseNotFound( "<H1>Must use a POST to update values</H1>" )

    data = request.raw_post_data

    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2

    now = long( time.time() )

    minute = now - now % 60 # make window 1 minutes long 
    cacheKey = "key2-ipTokenBucketMinute:%s/%s"%(ip,minute)
    token = memcache.incr( cacheKey , initial_value=0 )

    rateLimit = 100 # Max number of request per minute from each IP address
    if enableQuota and token >= rateLimit:
        if token == rateLimit:
            # should we log this or not
            logging.warning( "IP %s exceed per minute rate limit"%ip )
        return HttpResponseForbidden( "<H1>User has exceed limit of %d requests per minute</H1>"%rateLimit )
        
    logging.debug("Got post of alarm values %s from %s count=%d"%(data,ip, token) )
    addKnownIP( ip )
    
    try:
        jData = json.loads( data )
    except ValueError:
        logging.debug( "JSON data had error in parse")
        #return HttpResponse( content="<H1>JSON data had error in parse: %s </H1>"%e , mimetype=None,  status=400 )
        return HttpResponseNotFound( "<H1>JSON data had error in parse</H1>" )
    
    try:
        #TODO validate user input data here for security 
        logging.debug("j=%s"%str(jData) )
        logging.debug(" type is =%s"%str(type(jData)) )
        
        if ( type(jData) != dict ):
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
        cacheKey = "key2-alarmTokenBucketDay%s/%s"%(account,day)
        token = memcache.incr( cacheKey , initial_value=0 )
        win = now - now % (60) # make window 1 min long  
        cacheKey = "key2-alarmTokenBucketWindow%s/%s"%(account,win)
        token = memcache.incr( cacheKey , initial_value=0 )
        
        rateLimit = 10 # Max number of request per minute from each sensor
        if enableQuota and token >= rateLimit:
            if token == rateLimit:
                # should we log this or not
                logging.warning( "IP %s exceed per minute rate limit"%ip )
                return HttpResponseForbidden( "<H1>User has exceed limit of %d updates per minute for a sensor</H1>"%rateLimit )
                
        logging.debug("Received alarm account=%d user=%d eq=%d code=%d zone=%d part=%d"
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
            logging.debug("Sensor to enroll %s at IP %s "%(name,ip) ) 
            info = findEnroll( name, ip )
    
    except apiproxy_errors.OverQuotaError, message:
        logging.error( "Out of quota to store data in postSensorValues: %s"%message)
        return HttpResponseNotFound( "<H1>Out of quota to store data in postSensorValues</H1>" )
         
    return HttpResponse() # return a 200 


def postSensorValues(request):
    enableQuota = True 

    ver = os.environ['SERVER_SOFTWARE']
    devel = ver.startswith("Development")
    if ( devel ): 
        enableQuota = False # disable quotas for development environment

    if request.method != 'POST':
        return  HttpResponseNotFound( "<H1>Must use a POST to update values</H1>" )

    data = request.raw_post_data

    ip = request.META.get('REMOTE_ADDR') # works on google app engine 
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR') # Needed for webfaction proxy 
    if ( ip2 != None ):
        ip = ip2

    now = long( time.time() )

    minute = now - now % 60 # make window 1 minutes long 
    cacheKey = "key2-ipTokenBucketMinute:%s/%s"%(ip,minute)
    token = memcache.incr( cacheKey , initial_value=0 )

    rateLimit = 25 # Max number of request per minute from each IP address
    if enableQuota and token >= rateLimit:
        if token == rateLimit:
            # should we log this or not
            logging.warning( "IP %s exceed per minute rate limit"%ip )
        return HttpResponseForbidden( "<H1>User has exceed limit of %d requests per minute</H1>"%rateLimit )
        
    logging.debug("Got post of sensor values %s from %s count=%d"%(data,ip, token) )
    addKnownIP( ip )
    
    try:
        jData = json.loads( data )
    except ValueError:
        logging.debug( "JSON data had error in parse")
        #return HttpResponse( content="<H1>JSON data had error in parse: %s </H1>"%e , mimetype=None,  status=400 )
        return HttpResponseNotFound( "<H1>JSON data had error in parse</H1>" )
    
    try:
        #TODO validate user input data here for security 
        logging.debug("j=%s"%str(jData) )

        logging.debug(" type is =%s"%str(type(jData)) )

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

            joules = None  
            if m.has_key('j'):  # depricate 
                joules = float( m['j'] )

            if sensorExistsByName( name ):
                day = now - now % (24*3600) # make window 24 hours long  
                cacheKey = "key2-sensorTokenBucketDay%s/%s"%(name,day)
                token = memcache.incr( cacheKey , initial_value=0 )
                win = now - now % (60) # make window 1 min long  
                cacheKey = "key2-sensorTokenBucketWindow%s/%s"%(name,win)
                token = memcache.incr( cacheKey , initial_value=0 )

                rateLimit = 10 # Max number of request per minute from each sensor
                if enableQuota and token >= rateLimit:
                    if token == rateLimit:
                        # should we log this or not
                        logging.warning( "IP %s exceed per minute rate limit"%ip )
                    return HttpResponseForbidden( "<H1>User has exceed limit of %d updates per minute for a sensor</H1>"%rateLimit )
    
                logging.debug("Received measurment %s time=%d value=%s sum=%s units=%s joules=%s updateCount=%d"
                              %(name,mTime,value,sum,units,joules,token) ) 
                storeMeasurementByName( name, value, mTime=mTime, sum=sum, reset=False, joules=joules )
                addKnownIP( ip , name )
            else:
                logging.debug("Sensor to enroll %s at IP %s "%(name,ip) ) 
                info = findEnroll( name, ip )
    
    
        #sensorID= findSensorID( userName,sensorName, True ) #TODO - hack auto create new sensors 
        #if sensorID == 0 :
        #    return HttpResponseForbidden('<h1>Not a Valid sensor</h1>' )  
        #logging.debug( "Store user,sensor=%s,%s set to val=%s "%(userName,sensorName,data) )
        #storeMeasurement( sensorID,data)
    except apiproxy_errors.OverQuotaError, message:
        logging.error( "Out of quota to store data in postSensorValues: %s"%message)
        return HttpResponseNotFound( "<H1>Out of quota to store data in postSensorValues</H1>" )
         
    return HttpResponse() # return a 200 



def jsonFour(request,user):
    assert 0
    # stuff for daily pie chart 
    tqxParams = request.GET.get('tqx','')
    logging.info( "foo=%s", tqxParams )
    
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

    query = StreamIDInfo.all()
    query.filter( 'user =', user )
    results = query.fetch(1000)
    
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
                logging.debug( "Non numberic value in measurement value=%s"%( str(value) ) )

    html += "  ] } \n" #close rows, then table
    html += "} );\n" #close whole object 

    #response = HttpResponse("text/plain")
    response = HttpResponse()
    #response['Content-Disposition'] = 'attachment; filename=somefilename.csv'
    response.write( html );

    return response 


@digestLogin(realm='fluffyhome.com')
def login(request,user=None):
    return HttpResponseRedirect("/user/%s/status/"%user)


@digestLogin(realm='fluffyhome.com')
def enrollSensor2(request,sensorName,secret,user=None):
    return HttpResponseRedirect( "/user/%s/enroll/add/%s/"%(user,sensorName) )



#@digestLogin(realm='fluffyhome.com')
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
            logging.warning("Problem parsing out air temp from %s"%url )
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
            logging.warning("Problem parsing out wind speed from %s"%url )
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
            logging.warning("Problem parsing out update from %s"%url )
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
        logging.warning( "Problem fetching content for %s - reponse code = %s "%(url,result.status_code) )
        
    response = HttpResponse()
    response.write( html );
    return response 


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
            logging.warning("Problem parsing out air temp from %s"%url )
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
            logging.warning("Problem parsing out wind speed from %s"%url )
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
            logging.warning("Problem parsing out update from %s"%url )
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
        logging.warning( "Problem fetching content for %s - reponse code = %s "%(url,result.status_code) )
        
    response = HttpResponse()
    response.write( html );
    return response 


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
            logging.warning("Problem parsing out air temp from %s"%url )
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
            logging.warning("Problem parsing out wind speed from %s"%url )
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
            logging.warning("Problem parsing out update from %s"%url )
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
        logging.warning( "Problem fetching content for %s - reponse code = %s "%(url,result.status_code) )
        
    response = HttpResponse()
    response.write( html );
    return response 


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
            logging.warning("Problem parsing out air temp from %s"%url )
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
            logging.warning("Problem parsing out wind speed from %s"%url )
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
            logging.warning("Problem parsing out update from %s"%url )
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
        logging.warning( "Problem fetching content for %s - reponse code = %s "%(url,result.status_code) )
        
    response = HttpResponse()
    response.write( html );
    return response 
