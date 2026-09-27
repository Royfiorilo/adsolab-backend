-- migrate:up
-- version_id is numbered per investigation, so only the pair is unique.
ALTER TABLE kinetic_comparison DROP CONSTRAINT kinetic_comparison_version_id_key;
ALTER TABLE kinetic_comparison DROP CONSTRAINT kinetic_comparison_kinetic_investigation_id_key;
ALTER TABLE kinetic_comparison
    ADD CONSTRAINT kinetic_comparison_version_key UNIQUE (version_id, kinetic_investigation_id);

-- migrate:down
ALTER TABLE kinetic_comparison DROP CONSTRAINT kinetic_comparison_version_key;
ALTER TABLE kinetic_comparison
    ADD CONSTRAINT kinetic_comparison_kinetic_investigation_id_key UNIQUE (kinetic_investigation_id);
ALTER TABLE kinetic_comparison
    ADD CONSTRAINT kinetic_comparison_version_id_key UNIQUE (version_id);
