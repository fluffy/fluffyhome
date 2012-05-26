# Copyright (c) 2010, Cullen Jennings. All rights reserved.

from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to
from django.conf.urls import patterns, url, include

from store.views import *


from django.contrib import admin

admin.autodiscover()



urlpatterns = patterns('',
 
    (r'^wind/$', redirect_to, { 'url':'/wind/ab-south/'} ), 
    (r'^wind/ab-south/$', showAllWindSensors ), 
    (r'^wind/sensor/(?P<sensorName>[\w][\-\w]{0,64})/history/today/$', graphWindToday ), 

    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/sensors/$', showAllSensors ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/graphs/$', showGraphs ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/prefs/$', userPrefs ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/dump/$', dumpUser ), 

    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/enroll/add/(?P<sensorName>[\w][\-\w]{0,64})/$', addSensor ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/enroll/find/$', findSensorToEnroll ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/status/$', usage ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/history/(?P<sensorName>[\w][\-\w]{0,64})/(?P<type>[0-9a-zA-Z]{0,15})/(?P<period>[0-9a-zA-Z]{0,15})/json/$', usageJson ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/history/json/$', usageJson ), 

    (r'^sensor/(?P<userName>[a-zA-Z]\w{0,64})/(?P<sensorName>[\w][\-\w]{0,64})/create/$', createSensor ), 
    (r'^sensor/(?P<userName>[a-zA-Z]\w{0,64})/(?P<sensorName>[\w][\-\w]{0,64})/meta/$', editSensor ), 
    (r'^sensor/(?P<userName>[a-zA-Z]\w{0,64})/(?P<sensorName>[\w][\-\w]{0,64})/history/today/$', graphToday ), 
    (r'^sensor/(?P<userName>[a-zA-Z]\w{0,64})/(?P<sensorName>[\w][\-\w]{0,64})/history/today/json/$', todayJson ), 

    (r'^sensor/(?P<userName>[a-zA-Z]\w{0,64})/(?P<sensorName>[\w][\-\w]{0,64})/history/$', showLineGraph ), 
    (r'^sensor/(?P<userName>[a-zA-Z]\w{0,64})/(?P<sensorName>[\w][\-\w]{0,64})/history/csv/$', showLineGraphCSV ), 

    (r'^sensor/(?P<userName>[a-zA-Z]\w{0,64})/alarm/dump/(?P<year>[\d]{4,4})/(?P<day>[\d]{1,3})/$', dumpAlarm ), 

    (r'^sensor/(?P<userName>[a-zA-Z]\w{0,64})/(?P<sensorName>[\w][\-\w]{0,64})/dump/(?P<year>[\d]{4,4})/(?P<day>[\d]{1,3})/$', dumpSensor ), 

    (r'^sensorValues/$', postSensorValues ), 
    (r'^alarmValues/$', postAlarmValues ), 
 
    (r'^tasks/update/(?P<userName>[\*a-zA-Z]\w{0,64})/(?P<sensorName>[\*\w][\-\w]{0,64})/(?P<pTime>[0-9]{8}T[0-9]{6}Z)/$', updateValues ), 
    (r'^tasks/update/(?P<userName>[\*a-zA-Z]\w{0,64})/(?P<sensorName>[\*\w][\-\w]{0,64})/(?P<pTime>[\*])/$', updateValues ), 

    (r'^tasks/notify/(?P<userName>[\*a-zA-Z]\w{0,64})/(?P<sensorName>[\*\w][\-\w]{0,64})/$', updateNotify ), 

    (r'^tasks/refresh/(?P<userName>[a-zA-Z]\w{0,64})/$', loadAllSensors ), 

    (r'^tasks/thin/(?P<userName>[\*a-zA-Z]\w{0,64})/(?P<sensorName>[\*\w][\-\w]{0,64})/(?P<pTime>[\*])/$', thinValues ), 
    (r'^tasks/thin/(?P<userName>[\*a-zA-Z]\w{0,64})/(?P<sensorName>[\*\w][\-\w]{0,64})/(?P<pTime>[\-])/$', thinValues ), 
    (r'^tasks/thin/(?P<userName>[\*a-zA-Z]\w{0,64})/(?P<sensorName>[\*\w][\-\w]{0,64})/(?P<pTime>[0-9]{10})/$', thinValues ), 
 
    (r'^tasks/pollWindAB1/(?P<loc>[\*\w][\-\w]{0,64})/$', pollWindAB1 ), 
    (r'^tasks/pollWindAB2/(?P<loc>[\*\w][\-\w]{0,64})/$', pollWindAB2 ), 
    (r'^tasks/pollWindAB3/(?P<loc>[\*\w][\-\w]{0,64})/$', pollWindAB3 ), 
    (r'^tasks/pollWindAB4/(?P<loc>[\*\w][\-\w]{0,64})/$', pollWindAB4 ), 

    #(r'^admin/updateAll/$', updateAllValues ), 
    #(r'^admin/stats/$', showStats ), 
    #(r'^admin/dump/meta/$', dumpMeta ), 
    #(r'^admin/updateAllNow/$', updateAllValuesNow ), 
    #(r'^admin/patchHourly/$', patchHourly ), 
    #(r'^admin/patchHourlyCount/$', patchHourlyCount ), 
    #(r'^admin/user/(?P<userName>[a-zA-Z]\w{0,64})/$', editUser ), 

    (r'^admin/', include(admin.site.urls)),

    (r'^enroll/(?P<sensorName>[\w][\-\w]{0,64})/(?P<secret>[0-9a-fA-F]{1,32})/$', enrollSensor2 ), 

    (r'^$', about ), 
    (r'^about/$', about ), 
    #(r'^login/$', login ), 

    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}), 
)
