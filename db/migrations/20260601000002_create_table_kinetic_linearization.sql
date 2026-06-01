-- migrate:up
CREATE TABLE kinetic_linearization (
    linearization_id serial PRIMARY KEY,
    name varchar(100) NOT NULL,
    formula varchar(255) NOT NULL,
    description text NOT NULL,
    parameters json NOT NULL,
    constants varchar(5)[],
    kinetic_model_id integer NOT NULL REFERENCES kinetic_model(_id) ON DELETE CASCADE,
    latex_formula varchar(255) NOT NULL
);

-- migrate:down
DROP TABLE kinetic_linearization;
