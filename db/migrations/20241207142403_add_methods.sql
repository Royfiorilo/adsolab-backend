-- migrate:up
INSERT INTO method (name, code, description)
VALUES
('Levenberg-Marquardt (Gauss-Newton modificado)', 'leastsq', 'Levenberg-Marquardt (Gauss-Newton modificado)'),
('Adaptive Memory Programming for Global Optimization', 'ampgo','Adaptive Memory Programming for Global Optimization'),
('Nelder-Mead', 'nelder','Nelder-Mead'),
('Gradiente Conjugado','cg','Gradiente Conjugado'),
('COBYLA','cobyla','COBYLA'),
('Basinhopping','basinhopping','Basinhopping')

-- migrate:down

