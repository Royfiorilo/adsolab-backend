from dataclasses import dataclass


@dataclass
class Adsorbate:
    id : int
    ion_name : str
    IUPAC_name : str
    formula : str

