#!/usr//bin/python                                                                                                      
import sys
import getopt
import time 
import RPi.GPIO as GPIO


def on():
    print "Turn On"

    # first make sure it is off
    GPIO.output(25, GPIO.HIGH)
    time.sleep( 0.5 ) # delay for 0.5 seconds 
    GPIO.output(25, GPIO.LOW)

    time.sleep( 1.0 )

    # now turn it on 
    GPIO.output(25, GPIO.HIGH)
    time.sleep( 3.0 ) # delay for 3 seconds 
    GPIO.output(25, GPIO.LOW)


def off():
    print "Turn Off"
    GPIO.output(25, GPIO.HIGH)
    time.sleep( 0.5 ) # delay for 0.5 seconds 
    GPIO.output(25, GPIO.LOW)


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "", ["help","on","off","version"])
        except getopt.GetoptError, msg:
             raise Usage(msg)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(25, GPIO.OUT)
        GPIO.output(25, GPIO.LOW)

        for opt,arg in opts:
            if opt in ( '--version' ):
                print('RPi.GPIO Version',GPIO.VERSION)
                print('Board revision -', GPIO.RPI_REVISION)
                print('Program version 0.0.1')
            if opt in ( '--on' ):
                on()
            if opt in ( '--off' ):
                off()
            if opt in ( '--help' ):
                print "run this program with option of --on or --off"

        GPIO.cleanup()
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())

