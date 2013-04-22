"""Integration with pyramid
"""
from __future__ import absolute_import

from pyramid.response import Response

from ._request import Request


def from_webob_request(request):
    path = filter(None, request.path.split('/'))
    trailing_slash = request.path.endswith('/')
    authenticated_user_id = None
    return Request(method=request.method,
                   path=path,
                   trailing_slash=trailing_slash,
                   authenticated_user_id=authenticated_user_id)


class Integration(object):
    def __init__(self, app=None):
        self.app = app

    def __call__(self, request=None):
        request = from_webob_request(request)
        response = Response()
        response.body = self.app(**request)
        response.content_type = 'application/json'
        return response
