# Copyright (c) 2010, Cullen Jennings. All rights reserved.


from django.conf.urls.defaults import *

#from pachube.views import *
from store.views import *

urlpatterns = patterns('',
   # (r'^pachube/(?P<feed>\d{1,8})/(?P<stream>\d{1,3})/view/$', view1 ), 
   # (r'^pachube/(?P<feed>\d{1,8})/(?P<stream>\d{1,3})/json/$', json ), 
   # (r'^pachube/(?P<feed>\d{1,8})/(?P<stream>\d{1,3})/table/$', view3 ), 
   # (r'^pachube/(?P<feed>\d{1,8})/(?P<stream>\d{1,3})/chart/$', view4 ), 

    (r'^twitterCallback/$', twitterCallback ), 

    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/sensors/$', showAllSensors ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/graphs/$', showGraphs ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/prefs/$', userPrefs ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/dump/$', dumpUser ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/twitterLogin/$', twitterLogin ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/twitterLogout/$', twitterLogout ), 
    (r'^user/(?P<userName>[a-zA-Z]\w{0,64})/twitterVerify/$', twitterVerify ), 
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

    (r'^sensorValues/$', postSensorValues ), 
    (r'^alarmValues/$', postAlarmValues ), 
 
    (r'^tasks/update/(?P<userName>[\*a-zA-Z]\w{0,64})/(?P<sensorName>[\*\w][\-\w]{0,64})/(?P<pTime>[0-9]{8}T[0-9]{6}Z)/$', updateValues ), 
    (r'^tasks/update/(?P<userName>[\*a-zA-Z]\w{0,64})/(?P<sensorName>[\*\w][\-\w]{0,64})/(?P<pTime>[\*])/$', updateValues ), 
    (r'^tasks/notify/(?P<userName>[\*a-zA-Z]\w{0,64})/(?P<sensorName>[\*\w][\-\w]{0,64})/$', updateNotify ), 
    (r'^tasks/refresh/(?P<userName>[a-zA-Z]\w{0,64})/$', loadAllSensors ), 

    (r'^admin/updateAll/$', updateAllValues ), 
    (r'^admin/stats/$', showStats ), 
    (r'^admin/updateAllNow/$', updateAllValuesNow ), 
    (r'^admin/updateHourly/$', upgradeHourly ), 
    (r'^admin/user/(?P<userName>[a-zA-Z]\w{0,64})/$', editUser ), 

    (r'^enroll/(?P<sensorName>[\w][\-\w]{0,64})/(?P<secret>[0-9a-fA-F]{1,32})/$', enrollSensor2 ), 

    (r'^$', about ), 
    (r'^about/$', about ), 
    (r'^login/$', login ), 


   #old names 
    # (r'^enroll/(?P<streamName>[a-zA-Z][\-\w]{0,64})/$', enroll ), 

    #(r'^user/(?P<user>[a-zA-Z]\w{0,64})/status/elec/$', totalElec ), 
    #(r'^user/(?P<user>[a-zA-Z]\w{0,64})/status/json/$', jsonFour ), 

    # (r'^sensor/(?P<userName>[a-zA-Z]\w{0,64})/(?P<sensorName>[\w][\-\w]{0,64})/value/$', store ), 

    # (r'^store/(?P<userName>[a-zA-Z]\w{0,64})/(?P<sensorName>[\w][\-\w]{0,64})/$', storeNoAuth ), 
    # (r'^admin/', include('django.contrib.admin.urls')),
)
