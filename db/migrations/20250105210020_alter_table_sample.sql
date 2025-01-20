-- migrate:up
ALTER TABLE sample
ADD COLUMN adsorbate_id integer not null references adsorbate,
ADD COLUMN adsorbent_id integer not null references adsorbent,
ADD COLUMN temperature double precision,
ADD COLUMN measure_unit varchar(10);

-- migrate:down
ALTER TABLE sample
DROP COLUMN adsorbate_id,
DROP COLUMN adsorbent_id,
DROP COLUMN temperature,
DROP COLUMN measure_unit;