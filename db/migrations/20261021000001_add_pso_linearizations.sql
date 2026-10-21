-- migrate:up
INSERT INTO kinetic_linearization (name, formula, description, parameters, constants, kinetic_model_id, latex_formula)
VALUES
(
    'Linealización Pseudo-Segundo Orden Tipo 2',
    '1/qt = (1 / (k2 * qe**2)) * (1/time) + 1/qe',
    'Forma lineal Tipo 2 del modelo de pseudo-segundo orden: la gráfica de 1/qt vs 1/t produce una recta de pendiente 1/(k2·qe²) e intercepto 1/qe. Es una de las cuatro formas lineales correctas (Tran et al., 2017, Ec. 24). El punto t = 0 se descarta.',
    '{"x": "1/time", "y": "1/qt", "m": "1/(k2 * qe**2)", "b": "1/qe"}',
    ARRAY[]::varchar(5)[],
    (SELECT _id FROM kinetic_model WHERE name = 'Pseudo-Segundo Orden'),
    '\frac{1}{q_t} = \frac{1}{k_2 q_e^2} \frac{1}{t} + \frac{1}{q_e}'
),
(
    'Linealización Pseudo-Segundo Orden Tipo 3',
    'qt = -(1 / (k2 * qe)) * (qt/time) + qe',
    'Forma lineal Tipo 3 del modelo de pseudo-segundo orden: la gráfica de qt vs qt/t produce una recta de pendiente -1/(k2·qe) e intercepto qe. Es una de las cuatro formas lineales correctas (Tran et al., 2017, Ec. 25). El punto t = 0 se descarta.',
    '{"x": "qt/time", "y": "qt", "m": "-1/(k2 * qe)", "b": "qe"}',
    ARRAY[]::varchar(5)[],
    (SELECT _id FROM kinetic_model WHERE name = 'Pseudo-Segundo Orden'),
    'q_t = -\frac{1}{k_2 q_e} \frac{q_t}{t} + q_e'
),
(
    'Linealización Pseudo-Segundo Orden Tipo 4',
    'qt/time = -(k2 * qe) * qt + k2 * qe**2',
    'Forma lineal Tipo 4 del modelo de pseudo-segundo orden: la gráfica de qt/t vs qt produce una recta de pendiente -k2·qe e intercepto k2·qe², que es la velocidad inicial de adsorción h. Es una de las cuatro formas lineales correctas (Tran et al., 2017, Ec. 26). El punto t = 0 se descarta.',
    '{"x": "qt", "y": "qt/time", "m": "-k2 * qe", "b": "k2 * qe**2"}',
    ARRAY[]::varchar(5)[],
    (SELECT _id FROM kinetic_model WHERE name = 'Pseudo-Segundo Orden'),
    '\frac{q_t}{t} = -k_2 q_e \, q_t + k_2 q_e^2'
);

-- migrate:down
DELETE FROM kinetic_linearization WHERE name IN (
    'Linealización Pseudo-Segundo Orden Tipo 2',
    'Linealización Pseudo-Segundo Orden Tipo 3',
    'Linealización Pseudo-Segundo Orden Tipo 4'
);
