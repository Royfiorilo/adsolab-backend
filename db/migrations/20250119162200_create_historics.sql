-- migrate:up
CREATE TABLE version (
    version_id SERIAL PRIMARY KEY,
    iterations INTEGER ,
    steps INTEGER,
    seeds JSON[] NOT NULL,
    created_at TIMESTAMP NOT NULL,
    investigation_id INTEGER NOT NULL REFERENCES investigation(investigation_id)
);

CREATE TABLE comparison (
    comparison_id SERIAL PRIMARY KEY,
    heuristic JSON NOT NULL,
    ml JSON NOT NULL,
    version_id INTEGER NOT NULL REFERENCES version(version_id)
);

CREATE TABLE fitted_model (
    fitted_model_id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL,
    best_adjust VARCHAR(100) NOT NULL,
    adjustment_methods JSON[] NOT NULL,
    version_id INTEGER NOT NULL REFERENCES version(version_id)
);



-- migrate:down

DROP TABLE comparison;
DROP TABLE fitted_model;
DROP TABLE version;
