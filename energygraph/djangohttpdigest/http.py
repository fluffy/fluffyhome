"""
Fixes around django.http
"""

from django.http import HttpResponse

class HttpResponseNotAuthorized(HttpResponse):
    status_code = 401
