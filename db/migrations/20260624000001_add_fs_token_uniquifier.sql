-- migrate:up
ALTER TABLE "user" ADD COLUMN fs_token_uniquifier VARCHAR(64) UNIQUE;

-- migrate:down
ALTER TABLE "user" DROP COLUMN fs_token_uniquifier;
