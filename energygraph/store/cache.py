
import os
import sys
import urlparse
import logging
import redis

logger = logging.getLogger('energygraph')


class Memcache:
    """ Class to wrap some memory key value pair datastore """
    cache = None

    
    def __init__( self ):
        self.cache = None


    def connect( self ):
        url = "redis://localhost:6379"
        try:
            url = os.environ['REDISTOGO_URL'] 
        except KeyError:
            #print "Must set the'REDISTOGO_URL environment variable"
            #raise
            pass

        print "OS VAR: ", url

        urlparse.uses_netloc.append('redis')
        url = urlparse.urlparse( url )

        assert url.hostname is not None, "Problem with redis URL"
        
        self.cache = redis.StrictRedis(  host=url.hostname, port=url.port, password=url.password, db=0 )

        assert self.cache is not None, "Failed to connect to REDIS server"

        try:
            r = self.cache.incr( "energygraph-memcache-connects" )
        except redis.exceptions.ConnectionError:
            logger.error( "Can not connect to redis server - fatal" )
            self.cache = None
            raise
    
    def get( self, key ):
        logger.debug( "in cache get" )
        if self.cache is None:
            self.connect()
        logger.debug( "about to cache get key=%s"%key )
        r = self.cache.get( key )
        logger.debug( "cache.get( %s )=%s"%(key,r) )
        return r 
    
    
    def put( self, key, value , time ):
        if self.cache is None:
            self.connect()

        if value is None:
            value = "None"
            
        self.cache.set( key, value )

    
    def incr( self, key, expire ):
        if self.cache is None:
            self.connect()
        # if key does not exist, start with inital value of 0 
        r = self.cache.incr( key )
        r = int( r )
        if ( r == 1 ) :
            # key just got created, set the expire time
            self.cache.expire( key, expire )
        return r

    
    def delete( self, key  ):
        if self.cache is None:
            self.connect()
        self.cache.delete( key )

    
memcache = Memcache()
