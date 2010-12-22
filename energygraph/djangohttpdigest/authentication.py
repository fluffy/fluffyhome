"""
Various authentication cases, used by decorators.
"""

__all__ = ( "ModelAuthenticator" )

from hashlib import md5

from store.models import getUserPasswordHash

import logging


class Authenticator(object):
    """ Authenticator """
    
    def __init__(self):
        object.__init__(self)
        
        self.server_secret = None
        self.a1 = None
        self.a2 = None
    
    def get_a1(self, *args, **kwargs):
        """ Get server's a1 hash for later comparison """
        raise NotImplementedError("This (sub)class does not support this method, see another one.")
    
    def secret_passed(self, digestor):
        """ Compare computed secret to secret from authentication backend.
        If get_a1 was not called before, it's called with digestor as an argument.
        Return bool whether it matches.
        """
        if not self.a1:
            try:
                self.get_a1(digestor=digestor)
            except ValueError:
                return False
        
        assert self.a1 is not None
        
        client_secret = digestor.get_client_secret()
        server_secret = digestor.get_server_secret(a1=self.a1)
        return client_secret == server_secret




class ModelAuthenticator(Authenticator):
    def __init__(self,realm):
        Authenticator.__init__(self)
        self.realm = realm
        
    def get_a1(self, digestor):
        #try:
            pw = getUserPasswordHash(  digestor.get_client_username() )
            if pw is None:
                self.a1 = ""
            else:
                self.a1 = digestor.get_a1( self.realm,  digestor.get_client_username() , pw )
            return self.a1
        
        #except Exception, e:
        #    logging.debug("got exception %s"%e )
        #    raise e

