from model import Model


class Linearization(Model):
    def __init__(
            self,
            _id,
            name,
            formula,
            description,
            parameters,
            model_id=None
    ):
        super().__init__(_id, name, formula, description, parameters)
        self.model_id = model_id
