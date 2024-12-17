-- migrate:up
ALTER TABLE sample
ADD COLUMN title varchar(100),
ADD COLUMN description varchar(500);

-- migrate:down
ALTER TABLE sample
DROP COLUMN title,
DROP COLUMN description;
