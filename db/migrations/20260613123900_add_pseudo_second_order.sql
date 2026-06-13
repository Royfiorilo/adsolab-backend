-- migrate:up
INSERT INTO kinetic_model (name, formula, description, parameters, constants, latex_formula)
VALUES
(
    'Pseudo-Segundo Orden',
    'qt = (k2 * qe**2 * time) / (1 + k2 * qe * time)',
    'El modelo de pseudo-segundo orden, propuesto por Ho y McKay (1999), supone que la velocidad de adsorción depende del cuadrado de la diferencia respecto al equilibrio. Presenta excelente ajuste en muchos sistemas reales y está asociado a mecanismos de quimisorción.',
    '{"k2": "constante de velocidad de pseudo-segundo orden", "qe": "cantidad adsorbida en equilibrio"}',
    ARRAY[]::varchar(5)[],
    'q_t = \frac{k_2 q_e^2 t}{1 + k_2 q_e t}'
);

INSERT INTO kinetic_linearization (name, formula, description, parameters, constants, kinetic_model_id, latex_formula)
VALUES (
    'Linealización Pseudo-Segundo Orden',
    'time/qt = (1 / (k2 * qe**2)) + (1 / qe) * time',
    'Linealización del modelo de pseudo-segundo orden (t/qt vs t).',
    '{"x": "time", "y": "time/qt", "m": "1/qe", "b": "1/(k2 * qe**2)"}',
    ARRAY[]::varchar(5)[],
    (SELECT _id FROM kinetic_model WHERE name = 'Pseudo-Segundo Orden'),
    '\frac{t}{q_t} = \frac{1}{k_2 q_e^2} + \frac{1}{q_e} t'
);

-- migrate:down
DELETE FROM kinetic_linearization WHERE name = 'Linealización Pseudo-Segundo Orden';
DELETE FROM kinetic_model WHERE name = 'Pseudo-Segundo Orden';