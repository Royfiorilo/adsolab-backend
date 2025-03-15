-- migrate:up
ALTER TABLE model
ADD COLUMN constants varchar(5)[];

ALTER TABLE linearization
ADD COLUMN constants varchar(5)[];

UPDATE model
SET constants = ARRAY['R', 'T']
WHERE model.name = 'Temkin';


UPDATE linearization
SET constants = ARRAY['R', 'T']
WHERE linearization.name = 'Temkin Linearization';

-- migrate:down
ALTER TABLE model
DROP COLUMN constants;

ALTER TABLE linearization
DROP COLUMN constants;