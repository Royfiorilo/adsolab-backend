-- migrate:up
ALTER TABLE version
DROP COLUMN seeds;

ALTER TABLE fitted_model
ADD COLUMN seeds JSON[] NOT NULL;

ALTER TABLE comparison DROP CONSTRAINT comparison_version_id_fkey;
ALTER TABLE fitted_model DROP CONSTRAINT fitted_model_version_id_fkey;


ALTER TABLE version DROP CONSTRAINT version_pkey;
ALTER TABLE version ALTER COLUMN version_id DROP DEFAULT;
ALTER TABLE version ADD PRIMARY KEY (investigation_id, version_id);

ALTER TABLE comparison ADD COLUMN investigation_id INTEGER NOT NULL;
ALTER TABLE fitted_model ADD COLUMN investigation_id INTEGER NOT NULL;

ALTER TABLE comparison ADD CONSTRAINT comparison_version_id_fkey
FOREIGN KEY (version_id, investigation_id)
REFERENCES version(version_id, investigation_id)
ON DELETE CASCADE;

ALTER TABLE fitted_model ADD CONSTRAINT fitted_model_version_id_fkey
FOREIGN KEY (version_id, investigation_id)
REFERENCES version(version_id, investigation_id)
ON DELETE CASCADE;

-- migrate:down
ALTER TABLE version
DROP column seeds;

ALTER TABLE fitted_model
DROP COLUMN seeds;

ALTER TABLE version DROP CONSTRAINT version_pkey;
ALTER TABLE version ALTER COLUMN version_id DROP DEFAULT;
ALTER TABLE version ALTER COLUMN version_id SET DATA TYPE SERIAL;


ALTER TABLE version ADD PRIMARY KEY (version_id);


