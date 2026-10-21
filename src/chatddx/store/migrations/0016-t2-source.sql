-- Policy: a text is never changed; deleting is left to the admin's grants
-- (0015-t1-source.sql).
CREATE TRIGGER insert_only BEFORE UPDATE ON source.text
    FOR EACH ROW EXECUTE FUNCTION factor.refuse_change();
CREATE TRIGGER insert_only_truncate BEFORE TRUNCATE ON source.text
    FOR EACH STATEMENT EXECUTE FUNCTION factor.refuse_change();
