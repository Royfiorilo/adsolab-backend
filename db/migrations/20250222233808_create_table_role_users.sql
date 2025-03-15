-- migrate:up

create table roles_users
(
    user_id integer
        references "user",
    role_id integer
        references role
);

-- migrate:down

