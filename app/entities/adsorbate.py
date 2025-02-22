from dataclasses import dataclass


@dataclass
class Adsorbate:
    id : int
    ion_name : str
    iupac_name : str
    formula : str

