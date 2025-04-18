-- migrate:up
ALTER TABLE model
ADD COLUMN latex_formula varchar(255);

ALTER TABLE linearization
ADD COLUMN latex_formula varchar(255);

UPDATE model
SET latex_formula = '$q_e = \frac{q_{\max} \cdot k \cdot C_e}{1 + (k \cdot C_e)}$'
WHERE model.name = 'Langmuir';

UPDATE model
SET latex_formula = '$q_e = k_f \cdot C_e^{\frac{1}{n_f}}$'
WHERE model.name = 'Freundlich';

UPDATE model
SET latex_formula = '$q_e = \frac{q_{ms} \cdot k_s \cdot C_e^{\frac{1}{n_s}}}{1 + \left(k_s \cdot C_e^{\frac{1}{n_s}}\right)}$'
WHERE model.name = 'Sips';

UPDATE model
SET latex_formula = '$q_e = \frac{q_m \cdot C_e}{\left(k_t + C_e^{t_n}\right)^{\frac{1}{t_n}}}$'
WHERE model.name = 'Toth';

UPDATE model
SET latex_formula = '$q_e = \frac{R \cdot T}{b_{tk}} \ln(k_{tk} \cdot C_e)$'
WHERE model.name = 'Temkin';


UPDATE linearization
SET latex_formula = '$q_e = \frac{R \cdot T}{b_{tk}} \ln(k_{tk}) + \frac{R \cdot T}{b_{tk}} \ln(C_e)$'
WHERE linearization.name = 'Temkin Linearization';

UPDATE linearization
SET latex_formula = '$\log(q_e) = \log(k_f) + \frac{1}{n_f} \log(C_e)$'
WHERE linearization.name = 'Freundlich Linearization';

UPDATE linearization
SET latex_formula = '$\frac{1}{q_e} = \left(\frac{1}{k \cdot q_{\max}}\right) \cdot \frac{1}{C_e} + \frac{1}{q_{\max}}$'
WHERE linearization.name = 'Lineweaver-Burk Linearization';

UPDATE linearization
SET latex_formula = '$\frac{C_e}{q_e} = \frac{1}{q_{\max}} C_e + \frac{1}{q_{\max} k}$'
WHERE linearization.name = 'HaneseWoolf Linearization';

-- migrate:down
ALTER TABLE model
DROP COLUMN latex_formula;

ALTER TABLE linearization
DROP COLUMN latex_formula;