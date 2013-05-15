from __future__ import absolute_import

import json
import logging
import types

from metachao import aspect
from metachao.aspect import Aspect

from tpv.ordereddict import OrderedDict

from . import exceptions as exc


log = logging.getLogger('tpv.http')


class ipdb__call__(Aspect):
    @aspect.plumb
    def __call__(_next, self, **kw):
        import ipdb
        ipdb.set_trace()
        return _next(**kw)


class ipdb_GET(Aspect):
    @aspect.plumb
    def GET(_next, self, **kw):
        import ipdb
        ipdb.set_trace()
        return _next(**kw)


class ipdb_POST(Aspect):
    @aspect.plumb
    def POST(_next, self, **kw):
        import ipdb
        ipdb.set_trace()
        return _next(**kw)


class ipdb_PUT(Aspect):
    @aspect.plumb
    def PUT(_next, self, **kw):
        import ipdb
        ipdb.set_trace()
        return _next(**kw)


class ipdb_DELETE(Aspect):
    @aspect.plumb
    def DELETE(_next, self, **kw):
        import ipdb
        ipdb.set_trace()
        return _next(**kw)


class log_call(Aspect):
    @aspect.plumb
    def __call__(_next, self, **kw):
        log.info('%(method)s %(url)s' % kw +
                 ' %r', dict((k, v) for k, v in kw.items()
                             if k not in ('method', 'url')))
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
            response = json.dumps(getattr(e, 'body', None))
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
        id, node = self.traverse(url)
        attr = kw['query'].get('attr')

        if url.endswith('/'):
            return (
                self._render(k, v, attr) for k, v in node.items()
                if hasattr(v, 'keys')
            )
        else:
            return self._render(id, node)

    def _render(self, id, node, attr=None):
        response = OrderedDict(hasattr(v, 'keys') and (k, dict()) or (k, v)
                               for k, v in node.items()
                               if attr is None or k in attr)
        response['id'] = id
        return response

    def POST(self, url, data, **kw):
        """Add a new child, must not exist already
        """
        id, node = self.traverse(url)
        return node.add(data)

    def PUT(self, url, data, **kw):
        """Add/overwrite children - I guess
        """
        id, node = self.traverse(url)
        node.update(data)

    def DELETE(self, url, **kw):
        # node = self.traverse(url)
        # del node.parent[node.id]
        # XXX: or are we sending the delete to the parent and a list of ids?
        raise exc.NotImplemented

    def traverse(self, url):
        node = self.model
        path = filter(None, url.split('/'))
        id = None
        while path:
            id = path.pop(0)
            try:
                node = node[id]
            except KeyError:
                raise exc.NotFound
        return id, node
