from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KineticsLinearizationEntity:
    """Linealización asociada a un modelo cinético."""
    linearization_id: Optional[int] = None
    name: Optional[str] = None
    formula: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    constants: Optional[List[str]] = None
    kinetic_model_id: Optional[int] = None
    latex_formula: Optional[str] = None


@dataclass
class KineticsModelEntity:
    """
    Representa un modelo cinético de adsorción (e.g. Pseudo-primer orden,
    Pseudo-segundo orden, Difusión intraparticular).

    Tiene la misma estructura conceptual que `NoLinearModel` del módulo de
    equilibrio, pero la variable independiente es `time` y la dependiente `qt`.
    """
    _id: Optional[int] = None
    name: Optional[str] = None
    formula: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    constants: Optional[List[str]] = None
    latex_formula: Optional[str] = None
    linearizations: Optional[List[KineticsLinearizationEntity]] = field(default_factory=list)

    @property
    def id(self):
        return self._id

    def get_constants(self) -> List[str]:
        return self.constants if self.constants else []
