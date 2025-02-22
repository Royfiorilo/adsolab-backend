-- migrate:up
INSERT INTO linearization (name, formula, description, parameters, model_id)
VALUES
('Tempkin Linearization','qe = ((R*T)/btk) * log(ktk) + ((R*T)/btk) * log(ce)','Linealización del modelo de Tempkin', '{"x": "log(ce)", "y": "qe", "m":"((R*T)/btk)", "b":"((R*T)/btk) * log(ktk)"}', 4)

-- migrate:down

