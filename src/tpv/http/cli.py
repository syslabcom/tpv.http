from __future__ import absolute_import

import logging

from metachao import aspect
from metachao.aspect import Aspect


log = logging.getLogger('tpv.http.cli')


class log_call(Aspect):
    @aspect.plumb
    def __call__(_next, self, **kw):
        log.info('%s %s ' % (self.METHOD, kw.get('path', 'unknown')) +
                 '%r', dict((lambda n: (n, getattr(self, n, None)))
                            (swinfo.names[0].replace('-', '_'))
                            for swinfo in self._switches_by_func.itervalues()))
        return _next(**kw)
