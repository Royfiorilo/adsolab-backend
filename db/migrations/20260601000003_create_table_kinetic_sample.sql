-- migrate:up
CREATE TABLE kinetic_sample (
    kinetic_sample_id serial PRIMARY KEY,
    time float[] NOT NULL,
    qt float[] NOT NULL,
    concentration float[],
    initial_concentration float,
    volume float,
    adsorbent_mass float,
    title varchar(100),
    description varchar(500),
    temperature float,
    time_unit varchar(10),
    measure_unit varchar(10),
    adsorbate_id integer NOT NULL REFERENCES adsorbate(id),
    adsorbent_id integer NOT NULL REFERENCES adsorbent(id),
    user_id integer REFERENCES "user"(id),
    deleted_at timestamp
);

-- migrate:down
DROP TABLE kinetic_sample;
