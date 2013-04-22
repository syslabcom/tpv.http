class ResponseCode(Exception):
    pass

class BadRequest(ResponseCode):
    code = 400

class Unauthorized(ResponseCode):
    code = 401

class Forbidden(ResponseCode):
    code = 403

class NotFound(ResponseCode):
    code = 404

class MethodNotAllowed(ResponseCode):
    code = 405

class NotImplemented(ResponseCode):
    code = 501
