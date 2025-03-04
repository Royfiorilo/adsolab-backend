-- migrate:up
ALTER TABLE sample
ADD COLUMN deleted_at TIMESTAMP;

-- migrate:down
ALTER TABLE sample
DROP COLUMN deleted_at;
