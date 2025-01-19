-- migrate:up
INSERT INTO linearization (name, formula, description, parameters, model_id)
VALUES
('Tempkin Linearization','qe = ((r*t)/btk) * log(ktk) + ((r*t)/btk) * log(ce)','Linealización del modelo de Tempkin', '{"x": "log(ce)", "y": "qe", "m":"((r*t)/btk)", "b":"((r*t)/btk) * log(ktk)"}', 4)

-- migrate:down

