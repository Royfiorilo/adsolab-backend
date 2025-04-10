-- migrate:up
ALTER TABLE public.adsorbate
ADD CONSTRAINT unique_adsorbate UNIQUE (ion_name);

INSERT INTO public.adsorbate (ion_name, iupac_name, formula)
VALUES
  ('arseniato', 'arseniato (V)', 'AsO4'),
  ('cobre', 'cobre (II)', 'Cu'),
  ('cromato', 'cromato (VI)', 'CrO4'),
  ('fosfato', 'orto fosfato (VI)', 'PO4'),
  ('nitrato', 'nitrato (V)', 'NO3'),
  ('níquel', 'níquel (II)', 'Ni'),
  ('plata', 'plata (I)', 'Ag'),
  ('plomo', 'plomo (II)', 'Pb'),
  ('zinc', 'zinc (II)', 'Zn'),
('cadmio', 'cadmio (II)', 'Cd')
ON CONFLICT (ion_name) DO NOTHING;

ALTER TABLE public.adsorbent
ADD CONSTRAINT unique_adsorbent_name UNIQUE (name);

INSERT INTO public.adsorbent (name)
VALUES
  ('Azolla pinnata'),
  ('Carbón activado'),
  ('Carozo de palta'),
  ('Carozo de palta activado con ácido ortofosfórico'),
  ('Cáscara de banana'),
  ('Cáscara de maní'),
  ('Dolomita'),
  ('Hidroxiapatita'),
  ('Moringa oleifera Cascarilla de semilla'),
  ('Moringa oleifera rama y pedúnculos'),
  ('Moringa oleifera tronco'),
  ('Pistia stratiotes'),
  ('Residuo de la construcción Estructural'),
  ('Residuo de la construcción Mamposteria'),
  ('Salivinia molesta'),
  ('Ulva sativa alga patagónica')
ON CONFLICT (name) DO NOTHING;


