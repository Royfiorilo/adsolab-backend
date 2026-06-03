-- migrate:up
INSERT INTO kinetic_model (name, formula, description, parameters, constants, latex_formula)
VALUES
(
    'Difusión Intraparticular',
    'qt = kid * time**0.5 + C',
    'El modelo de difusión intraparticular (Weber-Morris) describe la adsorción cuando la difusión dentro de los poros del adsorbente es el mecanismo controlante de la velocidad. La linealización qt vs √t produce una recta cuya pendiente es kid; si el intercepto C es cero, la difusión intraparticular es el único mecanismo limitante. Cuando C ≠ 0, existe también resistencia en la capa límite externa.',
    '{"kid": "constante de velocidad de difusión intraparticular (mg/g·min^0.5), igual a la pendiente de la recta qt vs √t.", "C": "intercepto de la recta qt vs √t, relacionado con el espesor de la capa límite exterior (mg/g). Vale cero si la difusión intraparticular es el único mecanismo controlante."}',
    ARRAY[]::varchar(5)[],
    'q_t = k_{id} \cdot \sqrt{t} + C'
);

-- migrate:down
DELETE FROM kinetic_model WHERE name = 'Difusión Intraparticular';
