-- migrate:up
-- Names that differ only in case or spacing are the same material.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM adsorbate
        GROUP BY lower(regexp_replace(btrim(ion_name), '\s+', ' ', 'g'))
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'adsorbate has ion_name values that differ only in case or spacing: merge them before migrating';
    END IF;
    IF EXISTS (
        SELECT 1 FROM adsorbent
        GROUP BY lower(regexp_replace(btrim(name), '\s+', ' ', 'g'))
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'adsorbent has name values that differ only in case or spacing: merge them before migrating';
    END IF;
END $$;

CREATE UNIQUE INDEX adsorbate_ion_name_normalized_key
    ON adsorbate (lower(regexp_replace(btrim(ion_name), '\s+', ' ', 'g')));
CREATE UNIQUE INDEX adsorbent_name_normalized_key
    ON adsorbent (lower(regexp_replace(btrim(name), '\s+', ' ', 'g')));

-- migrate:down
DROP INDEX adsorbent_name_normalized_key;
DROP INDEX adsorbate_ion_name_normalized_key;
