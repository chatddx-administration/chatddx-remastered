-- Duplication: src/chatddx/store/queue.py: Status, and the writes that move a job between
-- them.
ALTER TABLE worker.job
    ADD CHECK (status IN ('queued', 'under way', 'finished', 'stopped', 'failed')),
    ADD CHECK (status <> 'queued' OR (worker IS NULL AND claimed IS NULL)),
    ADD CHECK (status <> 'under way' OR (worker IS NOT NULL AND claimed IS NOT NULL)),
    ADD CHECK ((status IN ('finished', 'stopped', 'failed')) = (ended IS NOT NULL)),
    ADD CHECK (status <> 'failed' OR why IS NOT NULL),
    ADD CHECK (score OR scorers IS NULL);

-- Policy: what a job is asked to do never changes; only how it stands does.
CREATE FUNCTION worker.keep_job() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (NEW.id, NEW.owner, NEW.run, NEW.endpoint, NEW.slots, NEW.score, NEW.scorers, NEW.queued)
        IS DISTINCT FROM
        (OLD.id, OLD.owner, OLD.run, OLD.endpoint, OLD.slots, OLD.score, OLD.scorers, OLD.queued)
    THEN
        RAISE EXCEPTION 'worker.job % may change only how it stands', OLD.id;
    END IF;
    IF OLD.status IN ('finished', 'stopped', 'failed') THEN
        RAISE EXCEPTION 'worker.job % has ended', OLD.id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER keep_job BEFORE UPDATE ON worker.job
    FOR EACH ROW EXECUTE FUNCTION worker.keep_job();
