-- src/chatddx/catalog/model.py: EntryField, Entry._shape, VARIED and REPLACED, and
-- check_varied in src/chatddx/catalog/threads.py.
-- A check passes when it is NULL, so NULL values are ruled out explicitly.
ALTER TABLE catalog.entry
    DROP CONSTRAINT entry_field_check,
    ADD CONSTRAINT entry_field_check CHECK (field IN (
        'name', 'description', 'tag', 'owner', 'collaborator', 'deleted', 'language',
        'varied', 'replaced'
    )),
    DROP CONSTRAINT entry_shape_check,
    ADD CONSTRAINT entry_shape_check CHECK (CASE field
        WHEN 'name' THEN person IS NULL AND CASE
            WHEN present THEN value IS NOT NULL AND value <> ''
            ELSE value IS NULL
        END
        WHEN 'description' THEN value IS NOT NULL AND person IS NULL AND present
        WHEN 'tag' THEN value IS NOT NULL AND value <> '' AND person IS NULL
        WHEN 'owner' THEN value IS NULL AND person IS NOT NULL AND present
        WHEN 'collaborator' THEN value IS NULL AND person IS NOT NULL
        WHEN 'deleted' THEN value IS NULL AND person IS NULL
        WHEN 'language' THEN value IS NOT NULL
            AND value ~ '^[a-z]{2,3}(-[A-Za-z0-9]{1,8})*$'
            AND person IS NULL AND present
        WHEN 'varied' THEN value IS NOT NULL
            AND value ~ '^[1-9][0-9]{0,17}$'
            AND person IS NULL AND present
        WHEN 'replaced' THEN value IS NOT NULL
            AND value ~ '^(instructions|few_shot|prompt|output|sampling|reasoning|passthrough|translations|toolset|engine)=(sha256:[0-9a-f]{64})?$'
            AND person IS NULL AND present
    END),
    ADD CONSTRAINT entry_run_check
        CHECK (field NOT IN ('varied', 'replaced') OR run IS NOT NULL);

CREATE FUNCTION catalog.check_varied() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    part text := split_part(NEW.value, '=', 1);
    held text := split_part(NEW.value, '=', 2);
    kinds text[] := CASE part
        WHEN 'engine' THEN ARRAY['engine.local', 'engine.remote']
        ELSE ARRAY['chunk.' || part]
    END;
BEGIN
    IF NEW.field = 'varied' AND NOT EXISTS (
        SELECT FROM catalog.edit WHERE id = NEW.value::bigint AND kind = 'skeleton'
    ) THEN
        RAISE EXCEPTION 'edit % is no configuration''s', NEW.value;
    END IF;
    IF NEW.field = 'replaced' AND held <> '' AND NOT EXISTS (
        SELECT FROM factor.component WHERE digest = held AND kind = ANY (kinds)
    ) THEN
        RAISE EXCEPTION '% isn''t a stored %', held, part;
    END IF;
    RETURN NEW;
END
$$;

-- A constraint trigger fires after the row's checks, so the value has its shape.
CREATE CONSTRAINT TRIGGER entry_varied AFTER INSERT ON catalog.entry
FOR EACH ROW WHEN (NEW.field IN ('varied', 'replaced'))
EXECUTE FUNCTION catalog.check_varied();
