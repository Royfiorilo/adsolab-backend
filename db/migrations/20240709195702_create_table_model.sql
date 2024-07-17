-- migrate:up
CREATE TABLE model (
    _id serial primary key,
    name varchar(100) not null,
    formula varchar(255) not null,
    description varchar(500),
    parameters json
);


-- migrate:down
DROP TABLE model
