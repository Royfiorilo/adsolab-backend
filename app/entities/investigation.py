R_CONSTANT = 8.3144598

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

    @property
    def constants(self):
        if not self.sample or not hasattr(self.sample, 'temperature'):
            raise ValueError("Sample has to have temperatura and not null")
        return {"T": self.sample.temperature, "R": R_CONSTANT}
