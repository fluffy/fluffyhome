#!/usr/bin/env python

# Copyright (c) 2009, Cullen Jennings
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this list
# of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
# 
# * Neither the name of Cullen Jennings nor the names of its contributors may be
# used to endorse or promote products derived from this software without specific
# prior written permission.
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


class TedRelay:
    port = 30303
    num = 1000
    sock = None
    tedIP = None
    tree = None

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
            if magic[0] == "TED5000" :
                print "Found TED5000 at IP Address %s"%ip
                self.tedIP = ip
                found = True
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

        #data = resp.read()
        self.tree = ElementTree()
        self.tree.parse( resp )
        resp.close()
        

    def power( self, mtuNum ):
        power = self.tree.find("Power")
        mtu = power.find("MTU%d"%mtuNum)
        p = mtu.find("PowerNow")
        v = float( p.text )
        print "found power mtu%d = %f"%(mtuNum,v)


    def shutdown(self):
        pass


def main():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-a", "--ted", dest="ip",
                      help="IP address of TED")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")

    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.error("incorrect number of arguments")
    if options.verbose:
        print "reading %s..." % options.filename

    relay = TedRelay(options.ip)
    relay.find()
    relay.fetch()
    relay.power(1)
    relay.power(2)

    
    relay.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
