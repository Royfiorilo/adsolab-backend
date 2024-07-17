class Linearization:
    def __init__(
            self,
            _id,
            name,
            formula,
            description,
            parameters,
            model_id = None
    ):
        self._id = _id
        self.name = name
        self.formula = formula
        self.description = description
        self.parameters = parameters
        self.model_id = model_id

    @property
    def id(self):
        return self._id
