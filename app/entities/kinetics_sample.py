from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional

R_CONSTANT = 0.0083144598


@dataclass
class KineticsSampleEntity:
    """
    Representa una muestra cinética de adsorción.

    La variable independiente es el tiempo (`time`) y la variable dependiente
    es la cantidad adsorbida en función del tiempo (`qt`).

    Opcionalmente puede almacenar la concentración en solución en cada punto
    temporal (`concentration`), junto con los parámetros necesarios para
    calcular `qt` a partir de datos de concentración.
    """

    time: List[float]
    qt: List[float]

    kinetic_sample_id: Optional[int] = None
    concentration: Optional[List[float]] = None
    initial_concentration: Optional[float] = None
    volume: Optional[float] = None
    adsorbent_mass: Optional[float] = None

    title: Optional[str] = None
    description: Optional[str] = None
    temperature: Optional[float] = None
    time_unit: Optional[str] = None
    measure_unit: Optional[str] = None

    adsorbate_id: Optional[int] = None
    adsorbent_id: Optional[int] = None
    user_id: Optional[int] = None
    deleted_at: Optional[datetime] = None

    @property
    def id(self):
        return self.kinetic_sample_id

    def remove(self, indexes: List[int]):
        """Elimina puntos experimentales por índice (equivalente a 'filter' del módulo de equilibrio)."""
        if not indexes:
            return
        self.time = [x for i, x in enumerate(self.time) if i not in indexes]
        self.qt = [x for i, x in enumerate(self.qt) if i not in indexes]
        if self.concentration:
            self.concentration = [x for i, x in enumerate(self.concentration) if i not in indexes]

    def len(self):
        return len(self.time)

    @property
    def constants(self):
        r = R_CONSTANT
        return {"T": self.temperature, "R": r}

    def create_sample_name(self, username: str, adsorbate_name: str, adsorbent_name: str) -> str:
        temperature = str(int(self.temperature)) if self.temperature else "?"
        gmt_minus_3 = timezone(timedelta(hours=-3))
        date = datetime.now(gmt_minus_3).strftime("%d-%m-%Y-%H:%M:%S")
        return f"{username}-{temperature}K-cinetica-{adsorbate_name}-{adsorbent_name}-{date}"
