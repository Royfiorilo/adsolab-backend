-- migrate:up
CREATE TABLE method (
    id serial primary key,
    name varchar(100) NOT NULL,
    code varchar(100) NOT NULL,
    description varchar(500) NOT NULL,
    color varchar(20)  NOT NULL
);

-- migrate:down

DROP TABLE method;
