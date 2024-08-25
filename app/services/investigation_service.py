from database import Investigation, Linearization, Sample
from entities.schemas.linearization_schema import LINEARIZATION_SCHEMA
from entities.schemas.sample_schema import SAMPLE_SCHEMA


def excecute_linearizations(investigation_id, linearizations, model):

    result = {"model": model}

    investigation = Investigation.with_schema(None).filter_by(
        investigation_id=investigation_id).first()
    sample = Sample.with_schema(SAMPLE_SCHEMA).filter_by(sample_id=investigation.sample_id).first()


    linearization_results = []
    for model_name in linearizations:
        linearization = Linearization.with_schema(LINEARIZATION_SCHEMA).filter_by(name=model_name).first()
        solution = linearization.run(sample)
        linearization_results.append(solution)
    result["linearizations"] = linearization_results
    return result

