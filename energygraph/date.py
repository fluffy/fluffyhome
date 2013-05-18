#!/usr/bin/env python

import datetime
import sys
from optparse import OptionParser

def main():
    usage = "usage: %prog <number time>"
    parser = OptionParser(usage, version="%prog 0.1")
    (options, args) = parser.parse_args()

    t = int( args[0] )
    tm = datetime.datetime.fromtimestamp( t )
    print tm
 

if __name__ == "__main__":
    sys.exit(main())
