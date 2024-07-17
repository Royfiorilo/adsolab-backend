-- migrate:up
create table linearization
(
    linearization_id serial primary key,
    name             varchar(100) not null,
    formula          varchar(255) not null,
    description      varchar(500) not null,
    parameters       json         not null,
    model_id         INTEGER REFERENCES model(pk_model) ON DELETE CASCADE
);

-- migrate:down
DROP TABLE linearization;
