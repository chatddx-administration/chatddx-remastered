REVOKE ALL ON ALL TABLES IN SCHEMA source FROM PUBLIC;
REVOKE ALL ON SCHEMA source FROM PUBLIC;

-- chatddx_reader gets nothing: the texts are vignettes. The writer gets no DELETE, so only
-- the admin deletes a text, to purge spam.
GRANT USAGE ON SCHEMA source TO chatddx_writer;
GRANT SELECT, INSERT ON source.text TO chatddx_writer;
