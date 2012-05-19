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
import optparse
import os 

import sqlite3 as sqlite 


class Graph():

    def __init__(self,):
        self.width = 400
        self.height = 150 
        self.altLabel = "tempature chart"

        self.tempMin=65
        self.tempMax=85 
        self.tempTick=5

        self.dbName = "/Library/Application Support/Perceptive Automation/Indigo 4/IndigoSqlClient/sqlite_db"

        self.now = 1257441969 # seconds since unix epoch to now  
        self.timeSpan = 24 * 60 * 60 # sixe of x axis in seconds 
        self.timeTick = 2 * 60 * 60
        self.timeMax = self.now + (self.timeTick - ( self.now % self.timeTick ) )
        self.timeMin = self.timeMax - self.timeSpan

        self.valid =  range(0,self.width)
        for i in range(0,self.width):
            self.valid[i] = False
        self.min = range(0,self.width)
        self.max = range(0,self.width)
        

    def dbSetup(self):
        self.db = sqlite.connect( self.dbName )

        cu = self.db.cursor()
        cu.execute('SELECT strftime("%s",ts ) AS "time" ,var_value FROM "variable_history" WHERE var_name="mainTemp" ORDER BY ts;')
        rows = cu.fetchall()
        for r in rows :
            x =  self.width * ( int(r[0]) - self.timeMin ) / self.timeSpan
            if ( x >= 0  and  x < self.width ):
                v = float(r[1])
                if ( self.valid[x] == False ):
                    self.valid[x] = True
                    self.min[x] = v
                    self.max[x] = v
                else:
                    if ( v < self.min[x] ):
                        self.min[x] = v
                    if ( v > self.max[x] ):
                        self.max[x] = v

        #if db only gets update when value changes, use values to fill right
        xNow = self.width * ( self.now - self.timeMin ) / self.timeSpan
        if ( xNow > self.width-1 ):
            xNow = self.width-1
        for s in range(0,xNow):
            if (self.valid[s] and not self.valid[s+1] ):
                self.valid[s+1] = True
                self.max[s+1] = self.max[s]
                self.min[s+1] = self.max[s]
                    


    def getValue(self, x, dataSet ):
        # time is seconds in the past from currnt time 
        # dataSet 0 is temp, 1 is set point, 2 is heat on/off , 3 is all zero 
        if ( dataSet == 3 ):
            return 0

        if ( dataSet == 2 ):
            return 0

        if ( dataSet == 1 ):
            return 70

        #return 70 +( ( x / 5 ) % 10 )
        if ( self.valid[x] == False ) :
            return -1000

        if ( x%2 == 0 ):
            return self.min[x]
        else:
            return self.max[x]



    def getEncodeValue(self, x , dataSet ):
        v = self.getValue( x , dataSet )

        if ( v == -1000 ):
            return "_"

        if (dataSet == 3 ):
            return 'A'

        if (dataSet == 2 ):
            if (v == 0 ):
                return 'A'
            return 'D'

        r = (v-self.tempMin) * 61.0 / (self.tempMax-self.tempMin)

        if ( r < 0.0 ):
            return '_' # _ indicates missing value
        if ( r > 61.0 ):
            return '_' # _ indicates missing value

        i = int(round(r))
        code = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        enc = code[i]
        return enc


    def plot(self, dataSet ):
        r = ""
        for x in range(0,self.width) :
            r +=  self.getEncodeValue( x, dataSet )
        return r
        
                
    def graph(self):
        print "<img src=\"http://chart.apis.google.com/chart?"
        print "&amp;chxt=x,y" #axis styles - this graph has x and y axis 
        print "&amp;chs=%dx%d"%(self.width,self.height) # size of resulting image 

        sys.stdout.write("&amp;chd=s:") # the values to graph 
        for d in range(0,4) :
            if ( d != 0 ):
                sys.stdout.write(",")
            sys.stdout.write(self.plot(d))
        print ""
        
        print "&amp;chdl=Temp|Set|" # lables for graphs 
        print "&amp;chls=3|1|0"  # style of lines graphs, first is 3 pixles wide, rest zero 
        print "&amp;chco=60B99A,69D2E760,00000000" # color os lines + alpha transparency
        #print "&amp;chm=b,69D2E760,0,1,0|b,D44222,3,2,0" #fill areas
        print "&amp;chm=b,D44222,3,2,0" #fill areas

        # print labels for axis 
        # print "&amp;chxl=0:|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|00|01|02|03|04|05|06|07|1:|65|70|75|80|85"
        sys.stdout.write("&amp;chxl=0:") # the axis label values
        for d in range(self.timeMin, self.timeMax + 1, self.timeTick ) :
            h = (d / (60*60)) % 24;
            sys.stdout.write("|%d"%h)
        sys.stdout.write("|1:")
        t = self.tempMin
        while ( t <= self.tempMax ):
            sys.stdout.write( "|%d"%(t) )
            t += 5
        print ""

        print "&amp;cht=lc\" alt=\"Tempature chart\">" # chart type is lc 



def main():

    graph = Graph()

    graph.dbSetup()

    print "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML//EN\"><html><head>"
    print "<title>Simple graph test</title>"
    print "</head><body>"

    print "<h1> Graph One </h1>"
   
    graph.graph()

    print "</body></html>"
    
    return 0


    
if __name__ == "__main__":
    sys.exit(main())


