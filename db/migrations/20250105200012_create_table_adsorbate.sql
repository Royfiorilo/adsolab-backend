-- migrate:up
CREATE TABLE adsorbate(
    id serial primary key,
    ion_name varchar(100) not null,
    iupac_name varchar(100) not null,
    --ion_charge integer not null,
    --ionic_radius integer not null,
    --dumping_limit integer not null,
    --CAS_number varchar(100),
    formula varchar(10) not null
    --formula_ion_charge varchar(10) not null,
    --molar_mass integer,
    --regulated boolean
);
-- migrate:down
DROP TABLE adsorbate