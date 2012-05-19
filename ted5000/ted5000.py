#!/usr/bin/env python

# Copyright (c) 2010, Cullen Jennings
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this list
#   of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
# 
# * Neither the name of Cullen Jennings nor the names of its contributors may be
#   used to endorse or promote products derived from this software without specific
#   prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import sys
import socket
import time 
import struct 
import httplib
from optparse import OptionParser
from xml.etree.ElementTree import ElementTree
from urlparse import urlparse


class TedClient:
    port = 30303
    num = 1000
    sock = None
    tedIP = None
    tree = None
    tedName = "TED5000"

    def __init__(self, pTedIP):
        if pTedIP is not None:
            self.tedIP = pTedIP
	pass

    def find(self):
        if self.tedIP is not None:
            print "Assuming TED is at IP Address %s"%self.tedIP
            return

	print "Listening for TED5000 broadcasts on port", self.port
	self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	self.sock.bind( ('',self.port) )
	print "Waiting for TED broadcast, may take up to 1 minute ..."

        found = False
	while not found:
	    data,(ip,port) = self.sock.recvfrom(1500)
	    magic = struct.unpack('!7s',data[0:7])
	    #print "magic header = '%s' from ip=%s"%(magic[0],ip)

            #i = 0
            #for d in data:
            #    print "data[%d] = %s"%(i,str(d) ) 
            #    i = i+1

            if magic[0] == "TED5000" :
                print "Found TED5000 at IP Address %s"%ip
                self.tedIP = ip
                found = True
                
                mac = struct.unpack('!17s',data[19:36])
                print "Mac address is %s"%mac
                self.tedName = "TED5000-%s"%mac


        self.sock.close()
	self.sock = None


    def fetch(self):
        self.tree = None

        ted = httplib.HTTPConnection(self.tedIP);
        ted.request("GET","/api/LiveData.xml")
        resp = ted.getresponse()
        if resp.status != 200:
            print "Could not fetch data from TED. Got HTTP Response %d %s"%(resp.status,resp.reason)
            resp.close()
            return

        self.tree = ElementTree()
        self.tree.parse( resp )
        resp.close()
        
    def numMTU(self):
        system = self.tree.find("System")
        nmtu =  system.find("NumberMTU")
        n = int( nmtu.text )
        return n

    def power( self, mtuNum ):
        power = self.tree.find("Power")
        mtu = power.find("MTU%d"%mtuNum)
        power = mtu.find("PowerNow")
        energy = mtu.find("PowerMTD")
        vpower = float( power.text )
        venergy = float( energy.text )
        #print "found power mtu%d power=%f energ=%f J"%(mtuNum,vpower,venergy)
        return (vpower,venergy)

    def shutdown(self):
        pass

    def name(self):
        return str(self.tedName)


def postJson( mtu, data, url, headers={} ):
    u = urlparse( url )

    headers["Content-Type"]="application/json"
    conn = httplib.HTTPConnection( u.netloc )
    conn.request("POST", u.path , data , headers )
    resp = conn.getresponse()

    if resp.status != 200:
        print "Problem posting to http://%s%s"%(u.netloc,u.path)
        print "%s %s"%(resp.status, resp.reason)


def main():
    usage = "usage: %prog [options] [URL]"
    parser = OptionParser(usage, version="%prog 0.1")
    parser.add_option("-t", "--loopTime", dest="loopTime", type="int", default=30,
                      help="How often in seconds to poll the TED")
    parser.add_option("-a", "--ted", dest="ip",
                      help="IP address of TED")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")
    parser.add_option("-x", "--headerName", dest="headerName", default=None,
                      help="HTTP Header Name to add to PUT request")
    parser.add_option("-y", "--headerValue", dest="headerValue", default="",
                      help="HTTP Header Value to add to PUT request")

    url = "http://www.fluffyhome.com/sensorValues/"

    (options, args) = parser.parse_args()
    if len(args) > 1:
        parser.error("incorrect number of arguments")
    if len(args) == 1:
        url = args[0]
 
    tedClient = TedClient(options.ip)
    tedClient.find()

    prev = [None,None,None,None,None,None,None]
    while True:
        tedClient.fetch()
        for mtu in range(1, tedClient.numMTU() + 1 ):
            (p,e) = tedClient.power(mtu)

            d=1000.0
            if prev[mtu] != None:
                d = float( p - prev[mtu] )
                if d < 0.0:
                    d = -d
            prev[mtu] = p

            if options.verbose:
                print "Got MTU%d is at %f watts (delta=%f)"%(mtu,p,d)

            if (d > 10.0) :
                headers = {}
                if options.headerName is not None:
                    headers[options.headerName] = options.headerValue 

                #post( mtu , p , args[0], h )
                data = '[ { "n":"%s-MTU%d" , "t":0, "v":%f, "s":%f } ]'%( tedClient.name(),mtu,p,e )
                                                                 
                if options.verbose:
                    print "Post %s to %s"%(data,url) 
                postJson( mtu , data , url, headers )

        time.sleep(options.loopTime)
    
    tedClient.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
