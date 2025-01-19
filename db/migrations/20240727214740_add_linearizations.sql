-- migrate:up
INSERT INTO linearization (name, formula, description, parameters, model_id)
VALUES
('HaneseWoolf Linearization', 'ce/qe = (1/qmax) * ce + 1 / (qmax * k)', 'Linealizacion del modelo de Langmuir', '{"x": "ce", "y": "ce/qe", "m": "1/qmax","b": "1/(qmax * k)"}', 1),
('Lineweaver-Burk Linearization', '1 / qe = (1 / k * qmax) * (1 / ce) + 1 / qmax', 'Linealizacion del modelo de Langmuir', '{"x": "1/ce", "y": "1/qe", "m": "1/(k*qmax)", "b": "1/qmax"}', 1),
('Freundlich Linearization', 'log(qe, 10) = log(kf, 10) + 1/nf * log(ce, 10)', 'Linealizacion del modelo de Freundlich', '{"x": "log(ce, 10)", "y": "log(qe, 10)", "m": "1 / nf", "b": "log(kf, 10)"}', 2)

-- migrate:down

