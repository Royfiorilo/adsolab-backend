-- migrate:up
INSERT INTO method (name, code, description, color)
VALUES
('Levenberg-Marquardt (Gauss-Newton modificado)', 'leastsq', 'Levenberg-Marquardt (Gauss-Newton modificado)', '#8F3237'),
('Adaptive Memory Programming for Global Optimization', 'ampgo','Adaptive Memory Programming for Global Optimization','#A133FC'),
('Nelder-Mead', 'nelder','Nelder-Mead','#FF71FC'),
('Gradiente Conjugado','cg','Gradiente Conjugado','#0000FF'),
('COBYLA','cobyla','COBYLA','#00FF00'),
('Basinhopping','basinhopping','Basinhopping', '#FF9300')

-- migrate:down

