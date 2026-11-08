-- Accommodating for runs from before, which name no canary set here, whatever their doc
-- says (0030-t2-ledger-canaries.sql).
ALTER TABLE ledger.run_stage ADD COLUMN canaries text REFERENCES factor.component;
