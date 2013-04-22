from .. import aspects


# XXX: add required init kws

@aspects.getattr_children
class Request(dict):
    pass
