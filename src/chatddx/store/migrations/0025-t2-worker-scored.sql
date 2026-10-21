ALTER TABLE worker.job
    ADD CHECK (score OR cardinality(scored) = 0),
    ADD CHECK (scorers IS NULL OR scored <@ scorers);

-- Policy: what a job is asked to do never changes, and what it has scored only grows; only
-- how it stands changes.
CREATE OR REPLACE FUNCTION worker.keep_job() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (NEW.id, NEW.owner, NEW.run, NEW.endpoint, NEW.slots, NEW.score, NEW.scorers, NEW.queued)
        IS DISTINCT FROM
        (OLD.id, OLD.owner, OLD.run, OLD.endpoint, OLD.slots, OLD.score, OLD.scorers, OLD.queued)
    THEN
        RAISE EXCEPTION 'worker.job % may change only how it stands', OLD.id;
    END IF;
    IF NOT (OLD.scored <@ NEW.scored) THEN
        RAISE EXCEPTION 'worker.job % keeps what it has scored', OLD.id;
    END IF;
    IF OLD.status IN ('finished', 'stopped', 'failed') THEN
        RAISE EXCEPTION 'worker.job % has ended', OLD.id;
    END IF;
    RETURN NEW;
END;
$$;
