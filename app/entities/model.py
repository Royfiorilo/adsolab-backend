class Model:
    def __init__(
            self,
            _id,
            name,
            formula,
            description,
            parameters,
            linealizations=None
    ):
        if linealizations is None:
            linealizations = []
        self._id = _id
        self.name = name
        self.formula = formula
        self.description = description
        self.parameters = parameters
        self.linealizations = linealizations

    @property
    def id(self):
        return self._id
