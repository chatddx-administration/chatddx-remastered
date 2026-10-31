-- Policy: one counter for the whole catalog, bumped by each transaction that writes to
-- it as it commits, so that what is held of the catalog is held while the counter
-- stands (src/chatddx/store/cache.py:catalogued). Bumped once per transaction and as
-- late as can be, so that writers wait on each other only as they commit.
CREATE TABLE catalog.version (
    one boolean PRIMARY KEY DEFAULT true CHECK (one),
    version bigint NOT NULL
);
INSERT INTO catalog.version (version) VALUES (0);

-- Accommodating for the writer, which may not update catalog.version itself: bumped as
-- the admin that made it.
CREATE FUNCTION catalog.bump_version() RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER SET search_path = pg_catalog AS $$
BEGIN
    IF current_setting('chatddx.catalog_bumped', true) IS DISTINCT FROM 'yes' THEN
        PERFORM set_config('chatddx.catalog_bumped', 'yes', true);
        UPDATE catalog.version SET version = version + 1;
    END IF;
    RETURN NULL;
END
$$;

DO $$
DECLARE
    t regclass;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'catalog.thread', 'catalog.edit', 'catalog.family', 'catalog.binding',
        'catalog.entry', 'catalog.label', 'catalog.language'
    ]::regclass[] LOOP
        EXECUTE format(
            'CREATE CONSTRAINT TRIGGER version AFTER INSERT ON %s '
            'DEFERRABLE INITIALLY DEFERRED '
            'FOR EACH ROW EXECUTE FUNCTION catalog.bump_version()', t);
    END LOOP;
END
$$;
