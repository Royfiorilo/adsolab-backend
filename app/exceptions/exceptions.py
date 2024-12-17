class BadRequestError(Exception):
    def __init__(self, message="Bad Request"):
        self.message = message
        super().__init__(self.message)

class NotFoundError(Exception):
    def __init__(self, message="Not Found"):
        self.message = message
        super().__init__(self.message)

class LinearizationError(Exception):
    def __init__(self, message="Error running linearization"):
        self.message = message
        super().__init__(self.message)

class FilterSampleError(Exception):
    def __init__(self, message="Error running filtering sample"):
        self.message = message
        super().__init__(self.message)