-- migrate:up

create table role
(
    id              serial
        primary key,
    name            varchar(80)             not null
        unique,
    description     varchar(255),
    permissions     text,
    update_datetime timestamp default now() not null
);

-- migrate:down

