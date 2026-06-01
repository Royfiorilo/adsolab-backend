-- migrate:up
CREATE TABLE kinetic_version (
    version_id integer NOT NULL,
    kinetic_investigation_id integer NOT NULL REFERENCES kinetic_investigation(kinetic_investigation_id) ON DELETE CASCADE,
    iterations integer,
    steps float,
    created_at timestamp DEFAULT now(),
    PRIMARY KEY (version_id, kinetic_investigation_id)
);

-- migrate:down
DROP TABLE kinetic_version;
