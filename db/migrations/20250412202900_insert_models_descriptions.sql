-- migrate:up
ALTER TABLE model
ALTER COLUMN description TYPE text;

ALTER TABLE linearization
ALTER COLUMN description TYPE text;

UPDATE model
SET description = '{"es":"Isoterma de Langmuir: Describe la adsorción en superficies homogéneas, donde los sitios de adsorción son equivalentes y las moléculas se adsorben de manera monomolecular. La isoterma alcanza un valor máximo Qmax cuando todos los sitios están ocupados.", "en": "Langmuir Isotherm: Describes adsorption on homogeneous surfaces, where adsorption sites are equivalent and molecules adsorb in a monolayer. The isotherm reaches a maximum Qmax when all sites are occupied."}',
    parameters = '{"qmax": {"es": "Capacidad máxima de adsorción, cantidad máxima de adsorbato que la superficie puede retener","en": "Maximum adsorption capacity, the maximum amount of adsorbate the surface can hold."}, "k": {"es": "Constante de Langmuir, relacionada con la afinidad de las moléculas por la superficie.","en": "Langmuir constant, related to the affinity of molecules for the surface."} }'
WHERE model.name = 'Langmuir';

UPDATE model
SET description = '{"es": "Isoterma de Freundlich: Describe la adsorción en superficies heterogéneas, donde los sitios tienen diferentes energías de adsorción. Es útil cuando la adsorción es no lineal y se distribuye de manera desigual.","en": "Freundlich Isotherm: Describes adsorption on heterogeneous surfaces, where sites have different adsorption energies. It is useful when adsorption is non-linear and unevenly distributed."}',
    parameters = '{"kf": {"es": "Constante que refleja la capacidad de adsorción en condiciones estándar.","en": "Constant reflecting adsorption capacity under standard conditions."}, "nf": {"es": "Exponente que indica la intensidad o la fuerza de adsorción (cuando n<1, la adsorción es favorable).","en": "Exponent indicating the intensity or strength of adsorption (when n<1, adsorption is favorable)."}}'
WHERE model.name = 'Freundlich';

UPDATE model
SET description = '{"es": "Isoterma de Sips: Es una combinación de las isotermas de Langmuir y Freundlich, adecuada para sistemas con superficies de adsorción mixtas (homogéneas y heterogéneas).","en": "Sips Isotherm: Combines the Langmuir and Freundlich isotherms, suitable for systems with mixed adsorption surfaces (both homogeneous and heterogeneous)."}',
    parameters = '{"qms": {"es": "Capacidad máxima de adsorción.","en": "Maximum adsorption capacity."}, "ks": {"es": "Constante relacionada con la energía de adsorción en el modelo de Sips.","en": "Constant related to the adsorption energy in the Sips model."}, "ns": {"es": "Exponente de Sips, que describe la heterogeneidad de la superficie y su relación con la capacidad de adsorción.","en": "Sips exponent, describing surface heterogeneity and its relationship with adsorption capacity."}}'
WHERE model.name = 'Sips';

UPDATE model
SET description = '{"es": "Isoterma de Toth: Modelo útil para sistemas con una gran heterogeneidad en la energía de adsorción. Ajusta mejor los datos experimentales en rangos de baja y media presión.","en": "Toth Isotherm: A model useful for systems with large heterogeneity in adsorption energy. It better fits experimental data at low to medium pressures."}',
    parameters = '{"qm": {"es": "Capacidad máxima de adsorción.","en": "Maximum adsorption capacity."}, "kt": {"es": "Constante de Toth, relacionada con la energía de adsorción en la superficie.","en": "Toth constant, related to the adsorption energy on the surface."}, "tn": {"es": "Exponente de Toth, que describe la distribución de la energía de adsorción.","en": "Toth exponent, describing the distribution of adsorption energy."}}'
WHERE model.name = 'Toth';

UPDATE model
SET description = '{"es": "Isoterma de Temkin: Este modelo considera la interacción entre las moléculas adsorbidas, lo que hace que la energía de adsorción disminuya de manera lineal con la cobertura. Es útil a bajas y medias presiones.","en": "Temkin Isotherm: This model considers interactions between adsorbed molecules, causing adsorption energy to decrease linearly with coverage. It is useful at low to medium pressures."}',
    parameters = '{"btk": {"es": "Es una constante relacionada con la distribución de la energía de adsorción. Un valor bajo de btk indica una distribución más uniforme de las energías de adsorción.","en": "The Temkin constant related to the adsorption energy. It reflects the distribution of adsorption energies on the surface. A lower btk value indicates a more uniform distribution of adsorption energies, while a higher value suggests more heterogeneity in energy levels."}, "ktk": {"es": "Es una constante que está relacionada con la afinidad del adsorbato por la superficie del adsorbente. Se puede obtener a partir de los datos experimentales.","en": "The Temkin constant associated with the affinity of the adsorbate for the surface. It is related to the adsorption capacity of the system. A higher ktk value indicates a greater affinity between the adsorbate and the adsorbent, leading to higher adsorption at lower concentrations."}}'
WHERE model.name = 'Temkin';


UPDATE linearization
SET description = '{"es": "La linealización de Temkin es un modelo usado para describir la adsorción de gases en superficies. Asume que la energía de adsorción varía linealmente con la cobertura, lo que convierte la ecuación en una forma logarítmica. Es útil en bajas y medias presiones.", "en": "Temkin linearization is a model used to describe gas adsorption on surfaces. It assumes adsorption energy varies linearly with coverage, making the equation logarithmic. It is useful at low to medium pressures."}'
WHERE linearization.name = 'Temkin Linearization';

UPDATE linearization
SET description = '{"es": "Se utiliza para describir la adsorción en superficies heterogéneas. Transforma la isoterma de adsorción en una forma lineal, permitiendo estimar parámetros como la capacidad de adsorción y la intensidad de adsorción", "en": "Used to describe adsorption on heterogeneous surfaces. It transforms the adsorption isotherm into a linear form, allowing the estimation of parameters like adsorption capacity and intensity."}'
WHERE linearization.name = 'Freundlich Linearization';

UPDATE linearization
SET description = '{"en": "A method used to analyze enzyme kinetics. It transforms the Michaelis-Menten equation into a straight line, making it easier to determine parameters such as Qmax and K.", "es": "Es un método utilizado para analizar datos de cinética enzimática. Convierte la ecuación de Michaelis-Menten en una línea recta, lo que facilita la determinación de parámetros como Qmax y K."}'
WHERE linearization.name = 'Lineweaver-Burk Linearization';

UPDATE linearization
SET description = '{"es": "Es una transformación de la ecuación de Michaelis-Menten que también permite obtener parámetros cinéticos. A diferencia de la de Lineweaver-Burk, presenta una distribución más uniforme de los datos a lo largo del eje x.", "en": "A transformation of the Michaelis-Menten equation that also allows for kinetic parameter determination. Unlike Lineweaver-Burk, it provides a more uniform data distribution along the x-axis"}'
WHERE linearization.name = 'HaneseWoolf Linearization';
