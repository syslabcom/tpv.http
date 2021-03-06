class ResponseCode(Exception):
    pass


class BadRequest(ResponseCode):
    code = 400

    def __init__(self, body=None):
        self.body = body


class Unauthorized(ResponseCode):
    code = 401


class Forbidden(ResponseCode):
    code = 403


class NotFound(ResponseCode):
    code = 404


class MethodNotAllowed(ResponseCode):
    code = 405


class InternalServerError(ResponseCode):
    code = 500


class NotImplemented(ResponseCode):
    code = 501
