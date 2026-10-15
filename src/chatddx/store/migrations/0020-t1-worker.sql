REVOKE ALL ON ALL TABLES IN SCHEMA worker FROM PUBLIC;
REVOKE ALL ON SCHEMA worker FROM PUBLIC;

GRANT USAGE ON SCHEMA worker TO chatddx_writer;

-- No default privileges: the tables are updated in place, so each one is granted
-- explicitly, and without DELETE, so that what was queued stays. chatddx_reader gets
-- nothing: why a job failed can quote what it was sending.
GRANT SELECT, INSERT, UPDATE ON worker.worker, worker.job, worker.control TO chatddx_writer;
