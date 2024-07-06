class FittedModel:
    def __init__(
            self,
            _id,
            params, statistics
    ):
        self._id = _id
        self.params = params
        self.statistics = statistics

    @property
    def id(self):
        return self._id
