
class CollibraAPIError(Exception):
    """Base exception for Collibra API errors"""
    def __init__(self, message, status_code=None, response_text=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class UnauthorizedError(CollibraAPIError):
    """Raised when authentication fails"""
    def __init__(self, message, status_code=401, response_text=None):
        super().__init__(message, status_code, response_text)


class ForbiddenError(CollibraAPIError):
    """Raised when access is forbidden"""
    def __init__(self, message, status_code=403, response_text=None):
        super().__init__(message, status_code, response_text)


class NotFoundError(CollibraAPIError):
    """Raised when resource is not found"""
    def __init__(self, message, status_code=404, response_text=None):
        super().__init__(message, status_code, response_text)


class ServerError(CollibraAPIError):
    """Raised when server returns 5xx errors"""
    def __init__(self, message, status_code=500, response_text=None):
        super().__init__(message, status_code, response_text)
