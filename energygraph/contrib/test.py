#!/usr/bin/env python

import oauth2 as oauth
from oauthtwitter import OAuthApi
import pprint

consumer_key = ""
consumer_secret = ""

access_tok = ""
access_tok_secret = ""

if access_tok == "":
    twitter = OAuthApi(consumer_key, consumer_secret)

    # Get the temporary credentials for our next few calls
    temp_credentials = twitter.getRequestToken()

    # User pastes this into their browser to bring back a pin number
    print(twitter.getAuthorizationURL(temp_credentials))
    
    oauth_verifier = raw_input('What is the Verifier? ')
    access_token = twitter.getAccessToken(temp_credentials, oauth_verifier)
    
    
    print("oauth access token: " + access_token['oauth_token'])
    print("oauth access token secret: " + access_token['oauth_token_secret'])
    
    access_tok = access_token['oauth_token']
    access_tok_secret = access_token['oauth_token_secret']
 
# Do a test API call using our new credentials
twitter = OAuthApi(consumer_key, consumer_secret, access_tok, access_tok_secret)

if True:
    res = twitter.VerifyCredentials()
    print( "User Name: " + res['name'] )
    print( "Status: " + res['status']['text'] )

if False:
    res = twitter.UpdateStatus("Test 2 with OAuth")
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(res)
