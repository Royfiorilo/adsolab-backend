from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Comparison:
    heuristic: dict
    ml: dict
    comparison_id: int = None


@dataclass
class FittedMethod:
    name: str
    params: dict
    statistics: dict
    residuals: dict

@dataclass
class FittedModel:
    model_id: int
    best_adjust: str
    adjustment_methods: List[FittedMethod]
    fitted_model_id: int = None


@dataclass
class Version:
    fitted_models: List[FittedModel]
    comparison: Comparison
    seeds: List[dict]
    investigation_id: int
    version_id:int =None
    iterations:int =None
    steps:int =None
    created_at:datetime = datetime.now()

