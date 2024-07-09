-- migrate:up
alter table model
    add column description varchar(500),
    add column parameters json;


-- migrate:down
ALTER TABLE model
    DROP COLUMN description,
    DROP COLUMN parameters;
