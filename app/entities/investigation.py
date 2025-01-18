class InvestigationEntity:
    def __init__(
            self,
            sample_id,
            investigation_id=None,
            fitted_models=None,
            sample =None
    ):
        self.investigation_id = investigation_id
        self.sample_id = sample_id
        self.fitted_models = fitted_models
        self.sample = sample
    @property
    def id(self):
        return self.investigation_id
