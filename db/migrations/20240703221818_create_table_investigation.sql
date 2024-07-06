-- migrate:up
create table  investigation
(
    investigation_id serial primary key,
    sample_id INTEGER REFERENCES sample(sample_id) ON DELETE CASCADE
);

-- migrate:down

DROP TABLE investigation;
