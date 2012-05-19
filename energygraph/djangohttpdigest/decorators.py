
#from django.http import HttpResponseBadRequest

#from djangohttpdigest.http import HttpResponseNotAuthorized
from djangohttpdigest.digest import Digestor, parse_authorization_header
from djangohttpdigest.authentication import  ModelAuthenticator


import logging

__all__ = ("digestProtect","digestLogin")


from djangohttpdigest.http import HttpResponse

class HttpResponseBadRequest(HttpResponse):
    def __init__(self, *args, **kwargs):
        HttpResponse.__init__(self, *args, **kwargs)
        self.status_code = 400

class HttpResponseNotAuthorized(HttpResponse):
    def __init__(self, *args, **kwargs):
        HttpResponse.__init__(self, *args, **kwargs)
        self.status_code = 401


def digestProtect( realm ):
    def _innerDecorator(function):
        def _wrapper(request, *args, **kwargs):
            
            digestor = Digestor(method=request.method, path=request.path, realm=realm)
            
            if request.META.has_key('HTTP_AUTHORIZATION'):
                try:
                    parsed_header = digestor.parse_authorization_header(request.META['HTTP_AUTHORIZATION'])
                except ValueError, err:
                    return HttpResponseBadRequest(err)
                
                authenticator = ModelAuthenticator(realm=realm)

                logging.info( "###################### Try authorization url user=%s   auth user=%s"%(
                        kwargs['userName'], digestor.get_client_username() ) )
                
                if authenticator.secret_passed(digestor):
                    if kwargs['userName'] ==  digestor.get_client_username() :
                        return function(request, *args, **kwargs)
                    else:
                        logging.error( "Bad authorization url user=%s   auth user=%s"%(
                                kwargs['userName'], digestor.get_client_username() ) )
                
            # nothing received, return challenge
            response = HttpResponseNotAuthorized("Not Authorized")
            response['www-authenticate'] = digestor.get_digest_challenge()
            return response
        return _wrapper
    return _innerDecorator


def digestLogin( realm ):
    def _innerDecorator(function):
        def _wrapper(request, *args, **kwargs):
            
            digestor = Digestor(method=request.method, path=request.path, realm=realm)
            
            if request.META.has_key('HTTP_AUTHORIZATION'):
                try:
                    parsed_header = digestor.parse_authorization_header(request.META['HTTP_AUTHORIZATION'])
                except ValueError, err:
                    return HttpResponseBadRequest(err)
                
                authenticator = ModelAuthenticator(realm=realm)

                logging.info( "###################### Try authorization as  auth user=%s"%(digestor.get_client_username() ) )
                
                if authenticator.secret_passed(digestor):
                    #kwargs['userName'] =  digestor.get_client_username() :
                    return function(request, user=digestor.get_client_username(), *args, **kwargs)
                
            # nothing received, return challenge
            response = HttpResponseNotAuthorized("Not Authorized")
            response['www-authenticate'] = digestor.get_digest_challenge()
            return response
        return _wrapper
    return _innerDecorator

