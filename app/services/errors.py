class ServiceError(Exception):
    """Generic error in the service layer."""

    def __init__(self, message: str, code: str = "service_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)
