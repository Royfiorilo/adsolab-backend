-- migrate:up
INSERT INTO linearization (name, formula, description, parameters, model_id)
VALUES
('Temkin Linearization','qe = ((R*T)/btk) * ln(ktk) + ((R*T)/btk) * ln(ce)','Linealización del modelo de Temkin', '{"x": "ln(ce)", "y": "qe", "m":"((R*T)/btk)", "b":"((R*T)/btk) * ln(ktk)"}', 4)

-- migrate:down

