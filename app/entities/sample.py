from datetime import datetime

R_CONSTANT = 0.0083144598

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SampleEntity:
    ce: List[float]
    qe: List[float]
    sample_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    temperature: Optional[float] = None
    measure_unit: Optional[str] = None
    adsorbate_id: Optional[int] = None
    adsorbent_id: Optional[int] = None
    deleted_at: Optional[str] = None
    user_id: Optional[int] = None

    @property
    def id(self):
        return self.sample_id

    def remove(self, indexes: List[int]):
        if not indexes:
            return
        self.ce = [x for i, x in enumerate(self.ce) if i not in indexes]
        self.qe = [x for i, x in enumerate(self.qe) if i not in indexes]

    def len(self):
        return len(self.ce)

    @property
    def constants(self):
        r = R_CONSTANT
        return {"T": self.temperature, "R": r}

    def create_sample_name(self, name, adsobate_name, adsobent_name):
        temperature = str(int(self.temperature))
        date = datetime.now().strftime("%d-%m-%Y-%H:%M:%S")

        return f"{name}-{temperature}K-{adsobate_name}-{adsobent_name}-{date}"
