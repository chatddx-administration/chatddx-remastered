-- src/chatddx/catalog/threads.py: check_edit repeats the position's check, and
-- src/chatddx/store/catalog.py:Catalog.edit writes an edit's labels with it.
-- An edit's labels are written in its transaction, by its writer: now() is the
-- transaction's start, so a label written later has another `at` than its edit.
CREATE OR REPLACE FUNCTION catalog.check_label() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    labelled catalog.edit;
    n integer;
BEGIN
    SELECT * INTO labelled FROM catalog.edit WHERE id = NEW.edit;
    -- `by` is quoted: unquoted, PL/pgSQL reads it as the BY of FOR ... BY.
    IF NEW."by" <> labelled."by" OR NEW.at <> labelled.at THEN
        RAISE EXCEPTION 'edit %: its labels are written with it, by its writer', NEW.edit;
    END IF;
    SELECT coalesce(jsonb_array_length(doc -> (NEW.part || 's')), 0) INTO n
    FROM factor.component WHERE digest = labelled.digest;
    IF NEW.position >= n THEN
        RAISE EXCEPTION '%: no % at position %', labelled.digest, NEW.part, NEW.position;
    END IF;
    RETURN NEW;
END
$$;

-- Triggers on the table 0017 replaced are gone with it; a store migrated to tier 0 first
-- has them already, from 0012.
DROP TRIGGER IF EXISTS label_position ON catalog.label;
CREATE TRIGGER label_position BEFORE INSERT ON catalog.label
FOR EACH ROW EXECUTE FUNCTION catalog.check_label();

DROP TRIGGER IF EXISTS insert_only ON catalog.label;
CREATE TRIGGER insert_only BEFORE UPDATE OR DELETE ON catalog.label
FOR EACH ROW EXECUTE FUNCTION factor.refuse_change();

DROP TRIGGER IF EXISTS insert_only_truncate ON catalog.label;
CREATE TRIGGER insert_only_truncate BEFORE TRUNCATE ON catalog.label
FOR EACH STATEMENT EXECUTE FUNCTION factor.refuse_change();
