-- migrate:up
INSERT INTO kinetic_linearization (name, formula, description, parameters, constants, kinetic_model_id, latex_formula)
VALUES (
    'Linealización PFO (Lagergren)',
    'ln(qe - qt) = ln(qe) - k1 * time',
    'Linealización del modelo de pseudo-primer orden (Lagergren). La gráfica de ln(qe - qt) vs tiempo produce una recta de pendiente -k1 e intercepto ln(qe). Para aplicar esta linealización es necesario conocer o estimar qe (capacidad de equilibrio). Si la recta muestra buen ajuste lineal (R² > 0.95), indica que el proceso sigue cinética de primer orden. Limitación: requiere que qe sea conocido o estimado correctamente, de lo contrario puede producir resultados incorrectos.',
    '{"x": "time", "y": "ln(qe - qt)", "m": "-k1", "b": "ln(qe)"}',
    ARRAY[]::varchar(5)[],
    (SELECT _id FROM kinetic_model WHERE name = 'Pseudo-Primer Orden (Lagergren)'),
    '\ln(q_e - q_t) = \ln(q_e) - k_1 \cdot t'
);

-- migrate:down
DELETE FROM kinetic_linearization WHERE name = 'Linealización PFO (Lagergren)';
