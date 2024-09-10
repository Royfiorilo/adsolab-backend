from .model import Model


class NoLinearModel(Model):

    def __init__(
            self,
            _id,
            name,
            formula,
            description,
            parameters,
            linearizations=None
    ):
        super().__init__(_id, name, formula, description, parameters)
        if linearizations is None:
            linearizations = []
        self.linearizations = linearizations

    def has_linearizations(self):
        return len(self.linearizations) == 0

    def get_linearizations(self):
        return self.linearizations

    def run(self, *args):
        return 0
