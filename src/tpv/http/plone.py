from __future__ import absolute_import

import json
import traceback
import urlparse

import plone.api
from StringIO import StringIO

from ZPublisher.HTTPResponse import status_reasons

from tpv.ordereddict import OrderedDict

from . import exceptions as exc
from ._request import Request


DATA_HANDLER = {
    "application/json": lambda request: json.loads(request.get('BODY')),
    "application/x-www-form-urlencoded": lambda request: request.form,
}


import logging
log = logging.getLogger('tpv.http.plone')


class Wrapper(object):
    """Wrapper to run tpv app from within plone

    We have knowledge about context and request, the real dispatcher
    doesn't.

    XXX: Once this code is stabilized it should be merged with the
    Traverser, i.e. become the Traverser View.

    """
    error = None

    def __init__(self, request, app):
        """Called from traverser.__init__

        request info needs to be extracted here as e.g. the path is
        not available anymore after __init__, within __call__

        """
        try:
            self._init(request=request, app=app)
        except (AttributeError, IndexError, KeyError, TypeError, NameError), e:
            self.error = 500
            log.error("%s\n%s" % (str(e), traceback.format_exc()))

    def _init(self, request, app):
        # extract needed information into a dictionary (the tpv request)
        # the zpublisher request is not to be needed from here on
        self.request = self._generate_tpv_request(request)

        # remember the zpublisher response to respond later
        self.zresponse = request.response

        # the tpv application we are wrapping for plone
        self.app = app

    def _generate_tpv_request(self, zrequest):
        method = zrequest.method
        if method == 'POST':
            method = zrequest.getHeader('X-Zope-Real-Method') or 'POST'

        url = '/' + '/'.join(reversed(zrequest.path))
        if zrequest.ACTUAL_URL.endswith('/'):
            url = url + '/'

        query_string = zrequest.QUERY_STRING
        query_list = urlparse.parse_qsl(query_string, keep_blank_values=True)
        query = OrderedDict()
        for k, v in query_list:
            query.setdefault(k, []).append(v)

        url_with_query = url
        if query_string:
            url_with_query += '?' + query_string

        if method in ('PUT', 'POST'):
            try:
                content_type = zrequest.CONTENT_TYPE.split(';')[0]
                handler = DATA_HANDLER[content_type]
            except (KeyError, ValueError), e:
                log.error("%s\n%s" % (str(e), traceback.format_exc()))
                self.error = 400
                self.error_body = 'Unknown content type: %s' % \
                                  zrequest.CONTENT_TYPE
                return
            else:
                try:
                    data = handler(zrequest)
                except ValueError, e:
                    log.error("%s\n%s" % (str(e), traceback.format_exc()))
                    self.error = 400
                    self.error_body = unicode(e)
                if not isinstance(data, basestring):
                    try:
                        data = OrderedDict(data)
                    except ValueError, e:
                        log.error("%s\n%s" % (str(e), traceback.format_exc()))
                        self.error = 400
                        self.error_body = unicode(e)
        else:
            data = None

        remoteip = zrequest.HTTP_X_REAL_IP

        return Request(
                data=data,
                environ={},
                getURL=lambda: url,
                method=method,
                query=query,
                remoteip=remoteip,
                stdin=StringIO(),
                url=url,
                url_with_query=url_with_query
        )

    def __call__(self):
        """Called from traverser.__call__

        Call tpv.http application and compile response
        """
        response_body = ""
        if not self.error:
            if plone.api.user.is_anonymous():
                authenticated_user_id = None
            else:
                # In case of a plone only user we will later on get an
                # error. This is to be expected.
                authenticated_user_id = plone.api.user.get_current().getId()

            # In case you were wondering: the user is not yet
            # available during __init__
            self.request['authenticated_user_id'] = authenticated_user_id

            try:
                status, response_body = self.app(**self.request)
            except Exception, e:
                log.error("%s\n%s" % (str(e), traceback.format_exc()))
                self.error = 500
            else:
                if status >= 400:
                    self.error = status

        if self.error:
            status = self.error

        self.zresponse.setStatus(status, lock=True)
        self.zresponse.setHeader('Content-Type', 'application/json')

        # make sure we are not getting cached (by IEx)
        self.zresponse.setHeader('Cache-Control',
                                 'no-cache, no-store, must-revalidate')
        self.zresponse.setHeader('Pragma', 'no-cache')
        self.zresponse.setHeader('Expires', '0')

        return response_body
