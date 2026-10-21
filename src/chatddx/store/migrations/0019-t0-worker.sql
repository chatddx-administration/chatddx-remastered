CREATE SCHEMA worker;

CREATE TABLE worker.worker (
    id uuid PRIMARY KEY,
    started timestamptz NOT NULL DEFAULT now(),
    seen timestamptz NOT NULL DEFAULT now()
);

-- Policy: what the run did is the ledger's; `stage` is a constant so that a foreign key can
-- point at the run's started row.
CREATE TABLE worker.job (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner bigint NOT NULL REFERENCES identity.person,
    run uuid NOT NULL,
    stage text NOT NULL DEFAULT 'started' CHECK (stage = 'started'),
    endpoint text NOT NULL,
    slots integer NOT NULL CHECK (slots >= 0),
    score boolean NOT NULL,
    scorers text[],
    status text NOT NULL DEFAULT 'queued',
    why text,
    halt boolean NOT NULL DEFAULT false,
    worker uuid REFERENCES worker.worker,
    queued timestamptz NOT NULL DEFAULT now(),
    claimed timestamptz,
    beat timestamptz,
    ended timestamptz,
    FOREIGN KEY (run, stage) REFERENCES ledger.run_stage
);
-- Policy: a run has one job queued or under way at a time.
CREATE UNIQUE INDEX job_open ON worker.job (run) WHERE status IN ('queued', 'under way');
CREATE INDEX job_waiting ON worker.job (queued, id) WHERE status IN ('queued', 'under way');
CREATE INDEX job_owner ON worker.job (owner, queued);

CREATE TABLE worker.control (
    owner bigint PRIMARY KEY REFERENCES identity.person,
    paused boolean NOT NULL DEFAULT false
);
