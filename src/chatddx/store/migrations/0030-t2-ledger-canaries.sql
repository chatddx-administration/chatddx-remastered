-- Accommodating for runs from before, which name none in the column: checked as rows are
-- added, not of those there are.
ALTER TABLE ledger.run_stage ADD CONSTRAINT run_stage_canaries
    CHECK (canaries IS NOT DISTINCT FROM doc->>'canaries') NOT VALID;
