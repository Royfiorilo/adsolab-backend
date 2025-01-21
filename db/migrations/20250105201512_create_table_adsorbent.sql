-- migrate:up
CREATE TABLE adsorbent (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
    --particle_size_range VARCHAR(50) NOT NULL,
    --surface_area DECIMAL(10, 4),
    --pore_volume DECIMAL(10, 4),
    --zero_charge_ph DECIMAL(10, 2),
    --impurities TEXT,
    --sample_origin TEXT,
    --chemical_formula VARCHAR(255),
    --species_name VARCHAR(255),
    --observations TEXT
);
-- migrate:down
DROP TABLE adsorbent