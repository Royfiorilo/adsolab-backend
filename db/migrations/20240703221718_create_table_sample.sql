-- migrate:up

create table  sample
(
    sample_id              serial primary key,
    ce               double precision[] not null,
    qe               double precision[] not null
);

-- migrate:down
DROP TABLE sample;
