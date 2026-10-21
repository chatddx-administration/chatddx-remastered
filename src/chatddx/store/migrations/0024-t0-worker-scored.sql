-- Policy: the scorers a job has finished, so that a job queued again mid-scoring scores
-- what is left.
ALTER TABLE worker.job ADD COLUMN scored text[] NOT NULL DEFAULT '{}';
