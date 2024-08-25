-- migrate:up

create table  sample
(
    sample_id              serial primary key,
    ce               real[] not null,
    qe               real[] not null
);

-- migrate:down
DROP TABLE sample;
