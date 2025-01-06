-- migrate:up
ALTER TABLE sample
ADD COLUMN adsorbate varchar(100),
ADD COLUMN adsorbent varchar(100),
ADD COLUMN temperature double precision,
ADD COLUMN mesuare_unit varchar(10);

-- migrate:down
ALTER TABLE sample
DROP COLUMN title,
DROP COLUMN description;
