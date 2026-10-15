-- migrate:up
INSERT INTO kinetic_model (name, formula, description, parameters, constants, latex_formula)
VALUES (
    'Elovich',
    'qt = (1/beta_elo) * ln(alpha_elo * beta_elo * time + 1)',
    'La ecuación de Elovich (Zeldowitsch, 1934) es un modelo empírico de dos parámetros que considera que la velocidad de adsorción disminuye exponencialmente a medida que aumenta la cantidad de adsorbato retenido: dqt/dt = α·e^(-β·qt). Integrada con qt = 0 a t = 0 da la expresión del modelo. Se emplea para describir quimisorción sobre superficies heterogéneas y su uso se extendió a la adsorción en fase acuosa (Ho, 2006). Referencia: García, J. I. (2018). Hidroxiapatita en el tratamiento de aguas arsenicales. Tesis de grado en Ingeniería Química, FIUBA.',
    '{"alpha_elo": "velocidad de adsorción inicial, cuando no hay adsorbato en la superficie. Unidades de qt por minuto (mg/g·min con qt en mg/g; mmol/g·min con qt en mmol/g).", "beta_elo": "constante cinética de adsorción, relacionada con el grado de cobertura de la superficie. Unidades inversas a las de qt (g/mg con qt en mg/g; g/mmol con qt en mmol/g)."}',
    ARRAY[]::varchar(5)[],
    'q_t = \frac{\ln(\alpha_{elo} \beta_{elo} t + 1)}{\beta_{elo}}'
);

INSERT INTO kinetic_linearization (name, formula, description, parameters, constants, kinetic_model_id, latex_formula)
VALUES (
    'Linealización Elovich',
    'qt = (1/beta_elo) * ln(alpha_elo * beta_elo) + (1/beta_elo) * ln(time)',
    'Linealización del modelo de Elovich. La gráfica de qt vs ln(t) produce una recta de pendiente 1/β e intercepto ln(α·β)/β. Es una aproximación válida cuando α·β·t es mucho mayor que 1, por lo que es menos exacta a tiempos cortos; el punto t = 0 se descarta porque ln(0) no está definido. Sus parámetros se usan como semillas del ajuste no lineal, que usa la ecuación completa.',
    '{"x": "ln(time)", "y": "qt", "m": "1/beta_elo", "b": "ln(alpha_elo * beta_elo)/beta_elo"}',
    ARRAY[]::varchar(5)[],
    (SELECT _id FROM kinetic_model WHERE name = 'Elovich'),
    'q_t = \frac{1}{\beta_{elo}} \ln(\alpha_{elo} \, \beta_{elo}) + \frac{1}{\beta_{elo}} \ln(t)'
);

-- migrate:down
DELETE FROM kinetic_linearization WHERE name = 'Linealización Elovich';
DELETE FROM kinetic_model WHERE name = 'Elovich';
