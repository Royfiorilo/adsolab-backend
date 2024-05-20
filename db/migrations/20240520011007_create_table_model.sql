-- migrate:up

CREATE TABLE model (
    id uuid NOT NULL,
    name varchar(100) NOT NULL,
    formula varchar(255) NOT NULL,
    CONSTRAINT pk_model PRIMARY KEY (id)
)

-- migrate:down

DROP TABLE model;

