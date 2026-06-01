"""
kinetics_linearization_service.py

Responsabilidad:
    Ejecutar las linealizaciones de modelos cinéticos cuando estén definidas.

    Equivalente a `linearization_service.py` del módulo de equilibrio, pero
    usando `time` / `qt` como variables en lugar de `ce` / `qe`.

    Este servicio es opcional en el primer alcance del módulo cinético;
    puede implementarse en una iteración posterior si Jorge/Silvia confirman
    que se requieren linealizaciones cinéticas (e.g. ln(qe - qt) vs t para PFO,
    t/qt vs t para PSO).

    TODO: implementar una vez que las linealizaciones cinéticas sean validadas.
"""


def run_kinetic_linearization(request_json: dict):
    """
    Ejecuta linealizaciones para los modelos cinéticos solicitados.

    Flujo equivalente a `run_linearization_models` de `investigation_service.py`:
      1. Recuperar muestra cinética.
      2. Para cada modelo y linealización definida: transformar datos (time, qt).
      3. Ajustar regresión lineal con scipy.stats.linregress.
      4. Resolver sistema de ecuaciones con SymPy para recuperar parámetros.
      5. Propagar incertidumbres mediante Jacobiano.

    TODO: implementar.
    """
    raise NotImplementedError(
        "run_kinetic_linearization: pending implementation."
    )
