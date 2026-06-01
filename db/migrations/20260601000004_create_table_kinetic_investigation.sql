-- migrate:up
CREATE TABLE kinetic_investigation (
    kinetic_investigation_id serial PRIMARY KEY,
    kinetic_sample_id integer NOT NULL REFERENCES kinetic_sample(kinetic_sample_id) ON DELETE RESTRICT,
    user_id integer REFERENCES "user"(id)
);

-- migrate:down
DROP TABLE kinetic_investigation;
