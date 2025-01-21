from dataclasses import dataclass


@dataclass
class FittedModel:
    fitted_model_id = None
    models : list
    investigation_id: int
