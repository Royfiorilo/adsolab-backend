-- migrate:up
INSERT INTO kinetic_linearization (name, formula, description, parameters, constants, kinetic_model_id, latex_formula)
VALUES (
    'Linealización Intraparticular',
    'qt = kid * time**0.5 + C',
    'Linealización del modelo de difusión intraparticular (Weber-Morris). La gráfica de qt vs √t produce una recta de pendiente kid e intercepto C. Si la recta pasa por el origen (C = 0), la difusión intraparticular es el único mecanismo controlante de la velocidad.',
    '{"x": "time**0.5", "y": "qt", "m": "kid", "b": "C"}',
    ARRAY[]::varchar(5)[],
    1,
    'q_t = k_{id} \cdot \sqrt{t} + C'
);

-- migrate:down
DELETE FROM kinetic_linearization WHERE name = 'Linealización Intraparticular';
