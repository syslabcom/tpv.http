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
        log.info('%(method)s %(url_with_query)s' % kw +
                 ' %r', dict((k, v) for k, v in kw.items()
                             if k not in ('method', 'url_with_query')))
        return _next(**kw)


class block_access_to_root(Aspect):
    @aspect.plumb
    def __call__(_next, self, **kw):
        if kw['url'] == '/':
            raise exc.Forbidden
        return _next(**kw)


class dispatch_http_method(Aspect):
    def __call__(self, method, **kw):
        try:
            response = self._call(method=method, **kw)
        except exc.ResponseCode, e:
            response = json.dumps(getattr(e, 'body', None))
            status = e.code
        else:
            if method == 'POST':
                status = 201
            elif response:
                status = 200
            else:
                status = 204

            try:
                if isinstance(response, types.GeneratorType):
                    response = [json.dumps(x) for x in response]
                    response = '[' + ', '.join(response) + ']'
                else:
                    response = json.dumps(response)
            except Exception, e:
                log.error('Error encoding json response:', e)
                status = 500
                response = ""

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


class filter_search(Aspect):
    criteria = aspect.aspectkw(criteria=None)
    base_criteria = aspect.aspectkw(base_criteria=None)

    def __iter__(self):
        return self.search(attrlist=[''])

    def itervalues(self):
        return self.search()

    def iteritems(self):
        return ((node.dn, node) for node in self.itervalues())

    @aspect.plumb
    def search(_next, self, **kw):
        return _next(criteria=self.criteria,
                     base_criteria=self.base_criteria, **kw)


class criteria_loads(Aspect):
    @aspect.plumb
    def GET(_next, self, **kw):
        criteria = kw['query'].get('criteria')
        if criteria:
            kw['query']['criteria'] = [json.loads(x) for x in criteria]
        return _next(**kw)


class map_http_methods_to_model(Aspect):
    """map GET/POST/PUT/DELETE to node methods
    """
    model = aspect.aspectkw(model=None)

    def GET(self, url, **kw):
        id, node = self.traverse(url)

        if url.endswith('/'):
            criteria = kw['query'].get('criteria')
            base_criteria = kw['query'].get('base_criteria')
            if criteria or base_criteria:
                node = filter_search(node, criteria=criteria,
                                     base_criteria=base_criteria)

            return node.iteritems()
        return node

    def POST(self, url, data, **kw):
        """Add a new child, must not exist already
        """
        id, node = self.traverse(url)
        return node.add(data)

    def PUT(self, url, data, **kw):
        """Add/overwrite children - I guess
        """
        id, node = self.traverse(url)
        try:
            node.update(data)
        except ValueError, e:
            raise exc.BadRequest(e.args[0])

    def DELETE(self, url, **kw):
        url, id = url.rsplit('/', 1)
        _, node = self.traverse(url)
        try:
            del node[id]
        except ValueError, e:
            raise exc.BadRequest(unicode(e))

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


class render(Aspect):
    @aspect.plumb
    def GET(_next, self, **kw):
        attr = kw['query'].get('attr')

        if kw['url'].endswith('/'):
            return (self._render(v._id, v, attr)
                    for k, v in _next(**kw)
                    if hasattr(v, 'keys'))
        else:
            node = _next(**kw)
            try:
                id = node._id
            except AttributeError:
                id = kw['url'].split('/')[-1]
            return self._render(id, node, attr)

    def _render(self, id, node, attr=None):
        response = OrderedDict(hasattr(v, 'keys') and (k, dict()) or (k, v)
                               for k, v in node.items()
                               if attr is None or k in attr)
        response['id'] = id
        return response
