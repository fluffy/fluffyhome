"""
Support for HTTP digest client.
"""

from md5 import md5
from django.test.client import Client

__all__ = ["HttpDigestClient"]

class HttpDigestClient(Client):
    """ Extend Django's client for HTTP digest support """
    
    def set_http_authentication(self, username, password, path):
        self.http_username = username
        self.http_password = password
        self.http_path = path
    
    def http_authenticate(self, response, method, queryargs=None):
        """
        Authenticate using HTTP digest and return our second request.
        If problem occurs and we cannot repeat our request, return original one.
        """
    
    def get(self, url, data=None, *args, **kwargs):
        data = data or {}
        response = Client.get(self, url, data, *args, **kwargs)
        if response.status_code == 401:
            return self.http_authenticate(response=response, method='get', queryargs=data)

    def post(self, url, *args, **kwargs):
        response = Client.post(self, url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        response = Client.put(self, url, *args, **kwargs)
        
    def delete(self, url, *args, **kwargs):
        response = Client.delete(self, url, *args, **kwargs)
        
    def options(self, url, *args, **kwargs):
        response = Client.options(self, url, *args, **kwargs)

    def head(self, url, *args, **kwargs):
        response = Client.head(self, url, *args, **kwargs)

