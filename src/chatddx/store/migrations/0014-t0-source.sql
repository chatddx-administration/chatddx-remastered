CREATE SCHEMA source;

CREATE TABLE source.text (
    source text NOT NULL,
    id text NOT NULL,
    text text NOT NULL CHECK (text <> ''),
    by bigint NOT NULL REFERENCES identity.person,
    at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source, id)
);
-- Dependency: src/chatddx/store/texts.py: Texts.typed_since counts a person's latest texts.
CREATE INDEX text_by ON source.text (by, at);
