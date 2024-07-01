import logging

class EvaluationEntity:
    def __init__(
        self,
        _id,
        sample=None
    ):

        if _id and sample:
            self._id = _id
            self.sample = sample
        else:
            logging.error("Investigation without sample")

    @property
    def id(self):
        return self._id

