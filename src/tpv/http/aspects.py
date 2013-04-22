from __future__ import absolute_import

import json
import logging

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


class dispatch_http_method(Aspect):
    def __call__(self, method, **kw):
        if method not in ('GET', 'POST', 'PUT', 'DELETE'):
            raise exc.MethodNotAllowed

        try:
            method = getattr(self, method)
        except AttributeError:
            raise exc.NotImplemented

        return json.dumps(method(**kw))


class view(Aspect):
    @aspect.plumb
    def iteritems(_next, self):
        for k, v in _next():
            if hasattr(v, 'keys'):
                v = dict()
            yield (k, v)


class map_http_methods_to_model(Aspect):
    """map GET/POST/PUT/DELETE to node methods
    """
    model = aspect.aspectkw(model=None)

    def GET(self, url, **kw):
        node = self.traverse(url)
        if url.endswith('/'):
            return [OrderedDict(view(x).iteritems()) for x in node.values()
                    if hasattr(x, 'keys')]
        return OrderedDict(view(node).iteritems())

    def POST(self, url, data, **kw):
        """Add a new child, must not exist already
        """
        node = self.traverse(url)
        return node.add(child)

    def PUT(self, url, data, **kw):
        """Add/overwrite children - I guess
        """
        node = self.traverse(url)
        node.update(children)

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
