-- migrate:up
CREATE TABLE kinetic_fitted_model (
    kinetic_fitted_model_id serial PRIMARY KEY,
    kinetic_model_id integer NOT NULL,
    best_adjust varchar(100) NOT NULL,
    adjustment_methods json[] NOT NULL,
    seeds json[] NOT NULL,
    version_id integer NOT NULL,
    kinetic_investigation_id integer NOT NULL,
    CONSTRAINT fk_kinetic_fitted_model_version
        FOREIGN KEY (version_id, kinetic_investigation_id)
        REFERENCES kinetic_version(version_id, kinetic_investigation_id)
        ON DELETE CASCADE
);

-- migrate:down
DROP TABLE kinetic_fitted_model;
