-- migrate:up

create table "user"
(
    fs_webauthn_user_handle varchar(64)
        unique,
    mf_recovery_codes       text,
    password                varchar(255),
    us_phone_number         varchar(128)
        unique,
    username                varchar(255)
        unique,
    us_totp_secrets         text,
    id                      serial
        primary key,
    email                   varchar(255)            not null
        unique,
    active                  boolean                 not null,
    fs_uniquifier           varchar(64)             not null
        unique,
    confirmed_at            timestamp,
    last_login_at           timestamp,
    current_login_at        timestamp,
    last_login_ip           varchar(64),
    current_login_ip        varchar(64),
    login_count             integer,
    tf_primary_method       varchar(64),
    tf_totp_secret          varchar(255),
    tf_phone_number         varchar(128),
    create_datetime         timestamp default now() not null,
    update_datetime         timestamp default now() not null
);

-- migrate:down

