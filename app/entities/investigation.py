class InvestigationEntity:
    def __init__(
            self,
            sample,
            investigation_id=None,
            fitted_models=None
    ):
        self.investigation_id = investigation_id
        self.sample = sample
        self.fitted_models = fitted_models

    @property
    def id(self):
        return self.investigation_id
