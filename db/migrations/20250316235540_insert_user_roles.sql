-- migrate:up

INSERT INTO role (name)
values ('ADMIN'),
       ('RESEARCHER')

-- migrate:down

