from database import Investigation, Linearization, Sample
from entities.schemas.linearization_schema import LINEARIZATION_SCHEMA
from entities.schemas.sample_schema import SAMPLE_SCHEMA


def compare_r2_linearizations(linearization1, linearization2):
    if not linearization1:
        return linearization2

    return linearization1 if abs(linearization1["statistics"]["r"]) >= abs(
        linearization2["statistics"]["r"]) else linearization2


def excecute_linearizations(investigation_id, linearizations, model):
    result = {"model": model}
    best_result = None
    investigation = Investigation.with_schema(None).filter_by(
        investigation_id=investigation_id).first()
    sample = Sample.with_schema(SAMPLE_SCHEMA).filter_by(sample_id=investigation.sample_id).first()

    linearization_results = []
    for model_name in linearizations:
        linearization = Linearization.with_schema(LINEARIZATION_SCHEMA).filter_by(name=model_name).first()
        solution = linearization.run(sample)
        linearization_results.append(solution)
        best_result = compare_r2_linearizations(best_result, solution)
        result["best_result"] = best_result["name"]
    result["linearizations"] = linearization_results
    return result
