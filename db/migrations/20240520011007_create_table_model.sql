-- migrate:up

CREATE TABLE model (
    id serial primary key,
    name varchar(100) NOT NULL,
    formula varchar(255) NOT NULL
)

-- migrate:down

DROP TABLE model;
