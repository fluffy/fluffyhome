#!/usr/bin/env python

import sys
from optparse import OptionParser
from xml.etree.ElementTree import *
import urllib2
from urllib import urlencode


def post( data, url, type, user, password ):
    #u = urlparse( url )
    auth_handler = urllib2.HTTPDigestAuthHandler()
    auth_handler.add_password(realm='fluffyhome.com',
                              uri=url,
                              user=user,
                              passwd=password)
    opener = urllib2.build_opener(auth_handler)
    opener.addheaders = [('User-agent', 'FluffyHomeUploadDump/0.1')]
    urllib2.install_opener(opener)
   
    req = urllib2.Request(url,data)
    req.add_header('Content-Type', type)
    r = None
    try:
        r = urllib2.urlopen(req)
    except urllib2.HTTPError, err:
        print "Post to %s failed with error code %s"%(url,err.code)
        print str(err)
        contents = err.read()
        fileName = "/tmp/err.html"
        f = open( fileName , 'w')
        f.write( contents )
        f.close()
        print "Wrote error to " + fileName
        exit( -1) 

    #print r.info()
    print "Post to %s was OK"%url
 

def main():
    usage = "usage: %prog [options] dumpFile [URL]"
    parser = OptionParser(usage, version="%prog 0.1")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")
    parser.add_option("-p", "--password", dest="password",
                      help="HTTP Digest password" , default="123456" )
    url = "http://www.fluffyhome.com"
    url = "http://localhost:8081"

    (options, args) = parser.parse_args()
    if len(args) > 2:
        parser.error("incorrect number of arguments")
    if len(args) < 1:
        parser.error("incorrect number of arguments")
 
    fileName = args[0]
    if len(args) == 2:
        url = args[1]
 
    print "Uploading %s to %s"%(fileName,url)
    
    tree = ElementTree(file=fileName)
    root = tree.getroot()
    assert root is not None

    user = root.find("user")
    assert user is not None

    userName = user.attrib.get("userName")

    # create the user 
    u = url + "/admin/user/" + userName + "/"
    post( None , u ,  "application/x-www-form-urlencoded" , "admin", "none" );

    # update the user record 
    email = user.attrib.get("email")
    attributes = user.items()
    data = urlencode( attributes )
    u = url + "/user/" + userName + "/prefs/"
    post( data , u ,  "application/x-www-form-urlencoded" , userName, options.password );

    # create the sensors 
    sensors = tree.findall("sensor")
    for sensor in sensors:
        sensorName = sensor.attrib.get("sensorName")

        attributes = sensor.items()
        data = urlencode( attributes )
        u = url + "/sensor/" + userName + "/" + sensorName + "/create/"

        post( data , u ,  "application/x-www-form-urlencoded" , userName, options.password );

    #create the meassurement data 
    count = 0
    data = ""
    measurements = tree.findall("measurement")
    for measurement in measurements:
        sensorName = str( measurement.attrib.get("sensor") )
        time = int( measurement.attrib.get("time") )
        value = float( measurement.attrib.get("value") )
        integral = float( measurement.attrib.get("integral") )
        joules = float( measurement.attrib.get("joules") )

        #print sensorName,time,value,integral
        
        if count == 0:
            data = "[\n"
        else:
            data += ", \n"

        data += '  { "n":"%s", "t":%d, "v":%f, "s":%f, "j":%f }'%(sensorName,time,value,integral,joules)
        count = count+1

        if count > 20 :
            data += "\n]\n"
            u = url + "/sensorValues/" 
            post( data , u , "application/json" , userName, options.password );
            count = 0
            data = ""
    if count > 0:
        data += "\n]\n"
        u = url + "/sensorValues/" 
        post( data , u , "application/json", userName, options.password );
        count = 0
        data = ""

    # update the hourly values 
    # todo - should do and get of /admin/updateAll/


if __name__ == "__main__":
    sys.exit(main())
