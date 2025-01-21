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
            constants =None,
            linearizations=None
    ):
        if linearizations is None:
            linearizations = []
        self._id = _id
        self.name = name
        self.formula = Formula(formula)
        self.description = description
        self.parameters = parameters
        self.linearizations = linearizations
        self.constants = constants

    @property
    def id(self):
        return self._id

    def run(self, *args):
        return self.formula.apply(*args)

