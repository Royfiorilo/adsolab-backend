-- migrate:up
INSERT INTO kinetic_model (name, formula, description, parameters, constants, latex_formula)
VALUES (
    'Pseudo-Primer Orden (Lagergren)',
    'qt = qe * (1 - exp(-k1 * time))',
    'El modelo de pseudo-primer orden (PFO) o ecuación de Lagergren describe procesos de adsorción controlados por difusión externa o transferencia de masa en la superficie del adsorbente. Asume que la velocidad de adsorción es proporcional al número de sitios desocupados. Es más adecuado para sistemas con baja concentración inicial o cuando el proceso se aproxima al equilibrio rápidamente.',
    '{"k1": "constante de velocidad de pseudo-primer orden (min^-1). Valores típicos: 0.001-0.5 min^-1.", "qe": "capacidad de adsorción en equilibrio (mg/g). Representa la cantidad máxima que puede ser adsorbida cuando el sistema alcanza el equilibrio."}',
    ARRAY[]::varchar(5)[],
    'q_t = q_e \cdot (1 - e^{-k_1 \cdot t})'
);

-- migrate:down
DELETE FROM kinetic_model WHERE name = 'Pseudo-Primer Orden (Lagergren)';
