-- migrate:up
CREATE TABLE kinetic_model (
    _id serial PRIMARY KEY,
    name varchar(100) NOT NULL,
    formula varchar(255) NOT NULL,
    description text NOT NULL,
    parameters json NOT NULL,
    constants varchar(5)[],
    latex_formula varchar(255) NOT NULL
);

-- migrate:down
DROP TABLE kinetic_model;
