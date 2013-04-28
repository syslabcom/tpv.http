from __future__ import absolute_import

import tpv.aspects

# XXX: add required init kws

@tpv.aspects.getattr_children
class Request(dict):
    pass
