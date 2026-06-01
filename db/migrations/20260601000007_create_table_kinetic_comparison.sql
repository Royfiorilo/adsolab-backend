-- migrate:up
CREATE TABLE kinetic_comparison (
    kinetic_comparison_id serial PRIMARY KEY,
    heuristic json NOT NULL,
    ml json,
    version_id integer NOT NULL UNIQUE,
    kinetic_investigation_id integer NOT NULL UNIQUE,
    CONSTRAINT fk_kinetic_comparison_version
        FOREIGN KEY (version_id, kinetic_investigation_id)
        REFERENCES kinetic_version(version_id, kinetic_investigation_id)
        ON DELETE CASCADE
);

-- migrate:down
DROP TABLE kinetic_comparison;
