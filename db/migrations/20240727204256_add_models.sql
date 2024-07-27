-- migrate:up
INSERT INTO model (name, formula, description, parameters)
VALUES
('langmuir', 'qe = qmax * k * ce / 1 + (k * ce)', 'El modelo de isoterma de Langmuir describe la adsorción de gases en carbón activado y se hizo extensivo a la adsorción en sistemas líquidos', '{"qmax": "es un parámetro que representa la máxima cantidad de adsorbato que se encuentra en la superficie cuando este cubre una monocapa sobre los sitios de adsorción."
, "k": "es la constante de equilibrio, vinculada a la relación entre las velocidades de adsorción y de desorción"}'),
('freundlich', 'qe = kf * ce**(1 /nf)', 'El modelo de isoterma de Freundlich es una ecuación empírica. Es la primera conocida de tipo no ideal y que no está restringida a la formación de una monocapa de adsorbato. Esencialmente, supone que la distribución energética de los sitios de adsorción es heterogénea de tipo exponencial', '{"kf": "es función de la energía de adsorción y de la temperatura, permitiendo esto estimar la capacidad de remoción que presenta el sólido en ese sistema", "nf": "determina la intensidad de las fuerzas de interacción adsorbente-adsorbato, y permite determinar si la adsorción se verá favorecida o no"}'),


-- migrate:down

