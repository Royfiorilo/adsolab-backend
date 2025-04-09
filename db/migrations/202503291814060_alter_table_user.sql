-- migrate:up
ALTER TABLE "user"
ADD COLUMN deleted_at TIMESTAMP;

-- migrate:down
ALTER TABLE "user"
DROP COLUMN deleted_at;
