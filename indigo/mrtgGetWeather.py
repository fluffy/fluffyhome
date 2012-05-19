#!/usr/bin/env python

import string
import sys
import optparse
import pywapi

# to install this you will need pywapi, you can do that via instructions at  
# http://code.google.com/p/python-weather-api/

def main():
  global options
  
  optionParser = optparse.OptionParser(version="%prog 0.1",
                                       description="Get weather in format approperate for MRTG",
                                       usage="%prog [options] city")
  optionParser.add_option('--verbose','-v',action='store_true')
  optionParser.add_option('--metric','-m',
                          action='store_true',
                          help="use metric values. Default is imperial")
  optionParser.add_option('--humidity','',
                          action='store_true',
                          help="Return relative humidity instead of temperature.")
  options, arguments = optionParser.parse_args()
  
  if ( len(arguments) != 1 ):
    optionParser.error("Must provide one city name such as 'Calgary,AB' ")
  
  if options.verbose:
    print "City is " + arguments[0]
  
  result = pywapi.get_weather_from_google( arguments[0] )

  if options.humidity:
    humRes = result['current_conditions']['humidity']
    hum = "%s"%humRes
    if options.verbose:
      print "Raw humidity string is " + hum
    h = int( float( hum.lstrip("Humidity: ").rstrip("%") )  )
    if options.verbose:
      print "Parsed humidity is %d"%h
    print "%d"%h
    print 0
    print 0
    print "OutsideHumidity"
  else:
    if options.metric:
      print result['current_conditions']['temp_c']
      print 0
      print 0
      print "OutsideTempCelcius"
    else:
      print result['current_conditions']['temp_f']
      print 0
      print 0
      print "OutsideTempFahrenheit"

  return 0

if __name__ == "__main__":
    sys.exit(main())
