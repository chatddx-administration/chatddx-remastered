-- Labels named a scorer digest, and now name the edit of a scorer thread they were written
-- with. The old rows are dropped rather than moved: a store from before holds v1 scorers,
-- which can't be read any more, and is rebuilt by loading its data sets again.
DROP TABLE catalog.label;

CREATE TABLE catalog.label (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    edit bigint NOT NULL,
    kind text NOT NULL DEFAULT 'scorer' CHECK (kind = 'scorer'),
    part text NOT NULL CHECK (part IN ('view', 'resource')),
    position integer NOT NULL CHECK (position >= 0),
    value text NOT NULL CHECK (value <> ''),
    by bigint NOT NULL REFERENCES identity.person,
    at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (edit, part, position),
    FOREIGN KEY (edit, kind) REFERENCES catalog.edit (id, kind)
);
