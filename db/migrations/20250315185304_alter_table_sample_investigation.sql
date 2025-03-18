-- migrate:up
ALTER TABLE sample
ADD COLUMN user_id INTEGER NOT NULL;

ALTER TABLE sample
ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES "user"(id);


ALTER TABLE investigation
ADD COLUMN user_id INTEGER NOT NULL;

ALTER TABLE investigation
ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES "user"(id);


-- migrate:down
ALTER TABLE sample
DROP COLUMN user_id;

ALTER TABLE investigation
DROP COLUMN user_id;
