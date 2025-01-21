-- migrate:up
ALTER TABLE model
ADD COLUMN constants varchar(5)[];

ALTER TABLE linearization
ADD COLUMN constants varchar(5)[];

UPDATE model
SET constants = ARRAY['r', 't']
WHERE model.name = 'Tempkin';


UPDATE linearization
SET constants = ARRAY['r', 't']
WHERE linearization.name = 'Tempkin Linearization';

-- migrate:down
ALTER TABLE model
DROP COLUMN constants;

ALTER TABLE linearization
DROP COLUMN constants;