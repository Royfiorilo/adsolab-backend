-- migrate:up
INSERT INTO linearization (name, formula, description, parameters, model_id)
VALUES
('HaneseWoolf Linearization', 'ce/qe = (1/qmax) * ce + 1 / (qmax * k)', 'Linealizacion del modelo de Langmuir', '{"qmax": "", "k": ""}', 1),
('Lineweaver-Burk linearization', '1 / qe = (1 / k * qmax) * (1 / ce) + 1 / qmax', 'Linealizacion del modelo de Langmuir', '{"qmax": "", "k": ""}', 1),
('Freundlich linearization', 'log(q) = log(kf) + 1/nf * log(ce)', 'Linealizacion del modelo de Freundlich', '{"kf": "", "nf": ""}', 2)

-- migrate:down

