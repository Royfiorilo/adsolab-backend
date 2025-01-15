-- migrate:up
create table  fitted_model
(
    fitted_model_id serial primary key,
    investigation_id INTEGER REFERENCES investigation(investigation_id),
    models integer[] not null
);

-- migrate:down

DROP TABLE fitted_model;