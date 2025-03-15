from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, TypedDict
from entities.sample import SampleEntity

@dataclass
class Transformed:
    x: list[float]
    y: list[float]



@dataclass
class Comparison:
    heuristic: dict
    ml: dict
    comparison_id: int = None


@dataclass
class FittedMethod:
    name: str
    params: list
    statistics: dict
    residuals: dict
    transformed: Transformed = None

@dataclass
class FittedModel:
    model_id: int
    best_adjust: str
    seeds: List[dict]
    adjustment_methods: List[FittedMethod]
    fitted_model_id: int = None



@dataclass
class Version:
    fitted_models: List[FittedModel]
    comparison: Comparison
    investigation_id: int
    version_id:int =None
    iterations:int =None
    steps:int =None
    created_at:datetime = datetime.now()
    sample: SampleEntity = None

    def to_dict(self):
        return asdict(self)
