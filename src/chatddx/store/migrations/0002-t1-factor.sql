-- Accommodating for roles, which are cluster-wide: another database may already have
-- created those every schema's tier 1 grants to, or be creating them at this moment, as the
-- tests' workers do.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'chatddx_writer') THEN
        BEGIN
            CREATE ROLE chatddx_writer NOLOGIN;
        EXCEPTION WHEN duplicate_object OR unique_violation THEN
            NULL;
        END;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'chatddx_reader') THEN
        BEGIN
            CREATE ROLE chatddx_reader NOLOGIN;
        EXCEPTION WHEN duplicate_object OR unique_violation THEN
            NULL;
        END;
    END IF;
END
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA factor FROM PUBLIC;
REVOKE ALL ON SCHEMA factor FROM PUBLIC;

GRANT USAGE ON SCHEMA factor TO chatddx_writer, chatddx_reader;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA factor TO chatddx_writer;
GRANT SELECT ON ALL TABLES IN SCHEMA factor TO chatddx_reader;

ALTER DEFAULT PRIVILEGES IN SCHEMA factor
    GRANT SELECT, INSERT ON TABLES TO chatddx_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA factor
    GRANT SELECT ON TABLES TO chatddx_reader;
