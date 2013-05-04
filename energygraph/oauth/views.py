# Copyright (c) 2013, Cullen Jennings. All rights reserved.

import logging
import urllib2
import json

from oauthlib.oauth2 import WebApplicationClient
from oauthlib.oauth2 import MissingTokenError

from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.http import HttpResponseGone


logger = logging.getLogger('energygraph')

oauthClientID = "6edd75c38fef0562a43e" # localhost 
oauthClientSecret = "TODO" # TODO - hide 
redirectURI = "http://127.0.0.1:8000/oauth/redir"


def start(request):

    oauthAuthUrl = "https://github.com/login/oauth/authorize"
    state = "1234"
    scope = ["user"] # this is a github specific scope # TODO - string should work here, consider patch 
    
    client = WebApplicationClient( oauthClientID )
    uri = client.prepare_request_uri( uri=oauthAuthUrl, redirect_uri=redirectURI, scope=scope, state=state )
    logger.debug( "oauth request URI is %s"%uri )
    return HttpResponseRedirect( uri )
   

def redir(request):
    client = WebApplicationClient( oauthClientID )

    # parse the Grant 
    uri =  request.build_absolute_uri()
    if False:
        if not request.is_secure(): # TODO - very bad, defeats all security blah blah blah
            uri = uri.replace( 'http', 'https' )
    resp = client.parse_request_uri_response( uri )
    logger.debug( "oauth resp is %s" % resp )

    # get the Access token 
    acccessTokenReqBody = client.prepare_request_body(
        oauthClientID,
        code=resp['code'],
        redirect_uri=redirectURI, # TODO - not clear this should be requried 
        client_secret=oauthClientSecret ) # TODO - patch to allow this in library 
    logger.debug( "oauth acccessTokenReqBody is %s" % acccessTokenReqBody )
    tokenUrl = "https://github.com/login/oauth/access_token"
    data = acccessTokenReqBody
    try:
        request = urllib2.Request( tokenUrl, data, headers={"Accept" : "application/json"})
        response = urllib2.urlopen( request )
    except urllib2.URLError as e:
        logger.debug( "Problem with HTTP request to provider: %s" % e.reason )
        return HttpResponseNotFound( "<H1>Problem getting the access token</H1>" )
    body =  response.read()
    code =  response.getcode()

    # parse the access token 
    logger.debug( "oauth code is %s" % code )
    logger.debug( "oauth body is %s" % body )
    accessToken = None 
    try:
        accessToken = client.parse_request_body_response( body )
    except MissingTokenError:
        logger.debug( "oauth problem with access token body - got %s" % body )
        return HttpResponseNotFound( "<H1>Problem: missing token in response to access token</H1>" )
    except ValueError:
        logger.debug( "oauth problem with access token body - got %s" % body )
        return HttpResponseNotFound( "<H1>Problem parsing access token</H1>" )
    logger.debug( "oauth accessToken is %s" % accessToken )

    # get the user data 
    userUrl = "https://api.github.com/user"
    headers = {}
    headers[ 'Accept' ] = "application/json"
    headers[ 'Authorization'] = "bearer "+accessToken['access_token'] 
    assert accessToken['token_type'] == 'bearer'
    logger.debug( "start HTTP request for user info to %s" % userUrl )
    try:
        request = urllib2.Request( userUrl, headers=headers )
        response = urllib2.urlopen( request )
    except urllib2.URLError as e:
        logger.debug( "Problem with HTTP request to provider: %s" % e.reason )
        return HttpResponseNotFound( "<H1>Problem getting user data</H1>" )

    #parse the user info 
    body =  response.read()
    code =  response.getcode()
    logger.debug( "oauth user code is %s" % code )
    logger.debug( "oauth user body is %s" % body )
    try:
        userInfo = json.loads( body )
    except ValueError as e:
        logger.debug( "JSON data had error in parse")
        return HttpResponseNotFound( "<H1>JSON data for user had error in parse</H1>" )
    logger.debug("User Info %s " % json.dumps( userInfo, indent=4 ) )

    userName = userInfo['login']
    return HttpResponse( "<H1>Logged on as: %s</H1>"%userName )

