-- migrate:up
ALTER TABLE investigation DROP CONSTRAINT investigation_sample_id_fkey;
ALTER TABLE investigation
ADD CONSTRAINT investigation_sample_id_fkey
FOREIGN KEY (sample_id) REFERENCES sample(sample_id);

ALTER TABLE version DROP CONSTRAINT version_investigation_id_fkey;

ALTER TABLE version
ADD CONSTRAINT version_investigation_id_fkey
FOREIGN KEY (investigation_id) REFERENCES investigation(investigation_id) ON DELETE CASCADE;


-- migrate:down


