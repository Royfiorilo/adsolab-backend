-- migrate:up

create table  sample
(
    sample_id              serial primary key,
    ce               integer[] not null,
    qe               integer[] not null
);

-- migrate:down
DROP TABLE sample;
