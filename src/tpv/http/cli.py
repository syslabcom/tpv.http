from __future__ import absolute_import

import json
import logging
import types

from metachao import aspect
from metachao.aspect import Aspect

import tpv.cli

from tpv.ordereddict import OrderedDict

from . import exceptions as exc
from .aspects import filter_search

log = logging.getLogger('tpv.http.cli')


def jsontype(x):
    return json.loads(x)


class log_call(Aspect):
    @aspect.plumb
    def __call__(_next, self, *args):
        log.info('%s %s ' % (self.METHOD, args[0]
                             if len(args) > 0 else "undefined") +
                 '%r', dict((lambda n: (n, getattr(self, n, None)))
                            (swinfo.names[0].replace('-', '_'))
                            for swinfo in self._switches_by_func.itervalues()))
        return _next(*args)


class block_access_to_root(Aspect):
    @aspect.plumb
    def __call__(_next, self, url):
        if url == '/':
            raise exc.Forbidden
        return _next(url)


class print_status_and_response(Aspect):
    @aspect.plumb
    def __call__(_next, self, url):
        self.method = self.METHOD

        try:
            response = _next(url)
        except exc.ResponseCode, e:
            response = json.dumps(getattr(e, 'body', None))
            status = e.code
        else:
            if self.method == 'POST':
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

        self.result = (status, response)
        # print "%d\n%s" % (status, response)


class map_http_methods_to_model(Aspect):
    """map GET/POST/PUT/DELETE to node methods
    """
    model = aspect.config(model=None)

    @aspect.plumb
    def __init__(_next, self, *args, **kw):
        _next(*args, **kw)

    criteria = tpv.cli.SwitchAttr(['--criteria'], argtype=jsontype, list=True)
    base_criteria = tpv.cli.SwitchAttr(['--base-criteria'], argtype=jsontype,
                                       list=True)

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


class map_http_methods_to_model_get(map_http_methods_to_model):
    def __call__(self, url):
        id, node = self.traverse(url)

        if url.endswith('/'):
            criteria = self.criteria
            base_criteria = self.base_criteria
            if criteria or base_criteria:
                node = filter_search(node, criteria=criteria,
                                     base_criteria=base_criteria)

            return node.iteritems()
        return node


class map_http_methods_to_model_post(map_http_methods_to_model):
    def __call__(self, url):
        """Add a new child, must not exist already
        """
        id, node = self.traverse(url)
        return node.add(self.data)


class map_http_methods_to_model_put(map_http_methods_to_model):
    def __call__(self, url):
        """Add/overwrite children - I guess
        """
        id, node = self.traverse(url)
        try:
            node.update(self.data)
        except ValueError, e:
            raise exc.BadRequest(e.args[0])


class map_http_methods_to_model_delete(map_http_methods_to_model):
    def __call__(self, url):
        url, id = url.rsplit('/', 1)
        _, node = self.traverse(url)
        try:
            del node[id]
        except ValueError, e:
            raise exc.BadRequest(unicode(e))


class render(Aspect):
    # XXX should the switch be moved to staralliance.api.cli.app.Get,
    # because it is also used in the attr_membership_attributes
    # aspect???
    @aspect.plumb
    def __init__(_next, self, *args):
        _next(*args)
        self.attr = None

    @tpv.cli.switch(['--attr'], argtype=str, list=True)
    def set_attr(self, attr):
        self.attr = attr

    @aspect.plumb
    def __call__(_next, self, url):
        attr = self.attr

        if url.endswith('/'):
            return (self._render(v._id, v, attr)
                    for k, v in _next(url)
                    if hasattr(v, 'keys'))
        else:
            node = _next(url)
            try:
                id = node._id
            except AttributeError:
                id = url.split('/')[-1]
            return self._render(id, node, attr)

    def _render(self, id, node, attr=None):
        response = OrderedDict(hasattr(v, 'keys') and (k, dict()) or (k, v)
                               for k, v in node.items()
                               if attr is None or k in attr)
        response['id'] = id
        return response
