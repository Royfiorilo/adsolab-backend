from .formula import Formula
from abc import ABC


class Model(ABC):

    def __init__(
            self,
            _id,
            name,
            formula,
            description,
            parameters,
            constants = None,
            linearizations=None
    ):
        if linearizations is None:
            linearizations = []
        if constants is None:
            constants = []
        self._id = _id
        self.name = name
        self._formula = Formula(formula)
        self.description = description
        self.parameters = parameters
        self.linearizations = linearizations
        self.constants = constants

    @property
    def id(self):
        return self._id

    @property
    def formula(self):
        return self._formula

    def run(self, **kargs):
        return self._formula.apply(**kargs)


