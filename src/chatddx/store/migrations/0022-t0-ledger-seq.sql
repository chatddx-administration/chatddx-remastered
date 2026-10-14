-- One counter across the ledger's tables, so that a run's rows, its scores' included, are
-- read back in the order they were written. Rows from before are numbered in no
-- particular order.
CREATE SEQUENCE ledger.seq;

ALTER TABLE ledger.run_stage ADD COLUMN seq bigint NOT NULL DEFAULT nextval('ledger.seq');
ALTER TABLE ledger.run_item ADD COLUMN seq bigint NOT NULL DEFAULT nextval('ledger.seq');
ALTER TABLE ledger.canary_call ADD COLUMN seq bigint NOT NULL DEFAULT nextval('ledger.seq');
ALTER TABLE ledger.score_stage ADD COLUMN seq bigint NOT NULL DEFAULT nextval('ledger.seq');
ALTER TABLE ledger.score_item ADD COLUMN seq bigint NOT NULL DEFAULT nextval('ledger.seq');

CREATE INDEX score_stage_run ON ledger.score_stage (run) WHERE run IS NOT NULL;
