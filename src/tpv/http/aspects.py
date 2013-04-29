from __future__ import absolute_import

import json
import logging
import types

from metachao import aspect
from metachao.aspect import Aspect

from tpv.ordereddict import OrderedDict

from . import exceptions as exc


log = logging.getLogger('tpv.http')


class log_call(Aspect):
    @aspect.plumb
    def __call__(_next, self, **kw):
        log.info('CALL: %r', kw)
        return _next(**kw)


class block_access_to_root(Aspect):
    @aspect.plumb
    def __call__(_next, self, **kw):
        if kw['url'] == '/':
            raise exc.Forbidden
        return _next(**kw)


SUCCESS_STATUS = dict(
    GET=200,
    POST=201,
    PUT=204,
    DELETE=204,
)


class dispatch_http_method(Aspect):
    def __call__(self, method, **kw):
        try:
            response = self._call(method=method, **kw)
        except exc.ResponseCode, e:
            response = ""
            status = e.code
        else:
            status = SUCCESS_STATUS[method]
        return status, response

    def _call(self, method, **kw):
        if method not in ('GET', 'POST', 'PUT', 'DELETE'):
            raise exc.MethodNotAllowed

        if kw['url'].endswith('/') and method != 'GET':
            raise exc.BadRequest

        try:
            method = getattr(self, method)
        except AttributeError:
            raise exc.NotImplemented

        response = method(**kw)
        if type(response) == types.GeneratorType:
            response = [json.dumps(x) for x in response]
            response = '[' + ', '.join(response) + ']'
        else:
            response = json.dumps(response)

        return response


# class view(Aspect):
#     @aspect.plumb
#     def iteritems(_next, self):
#         for k, v in _next():
#             if hasattr(v, 'keys'):
#                 v = dict()
#             yield (k, v)

#     def items(self):
#         return self.iteritems()


class map_http_methods_to_model(Aspect):
    """map GET/POST/PUT/DELETE to node methods
    """
    model = aspect.aspectkw(model=None)

    def GET(self, url, **kw):
        node = self.traverse(url)
        if url.endswith('/'):
            return (
                self._render(x) for x in node.values()
                if hasattr(x, 'keys')
            )
        return self._render(node)

    def _render(self, node):
        return OrderedDict(hasattr(v, 'keys') and dict() or (k, v)
                           for k, v in node.items())

    def POST(self, url, data, **kw):
        """Add a new child, must not exist already
        """
        node = self.traverse(url)
        return node.add(data)

    def PUT(self, url, data, **kw):
        """Add/overwrite children - I guess
        """
        node = self.traverse(url)
        node.update(data)

    def DELETE(self, url, **kw):
        # node = self.traverse(url)
        # del node.parent[node.id]
        # XXX: or are we sending the delete to the parent and a list of ids?
        raise exc.NotImplemented

    def traverse(self, url):
        node = self.model
        path = filter(None, url.split('/'))
        while path:
            try:
                node = node[path.pop(0)]
            except KeyError:
                raise exc.NotFound
        return node
