-- Duplication: src/chatddx/catalog/model.py: Entry._shape, where a description is taken
-- away as a name is.
-- Accommodating for a check, which passes when it is NULL: NULL values are ruled out
-- explicitly.
-- Accommodating for a store holding an empty description, which the API wrote before a
-- description could be taken away: NOT VALID leaves the rows already written unchecked.
ALTER TABLE catalog.entry
    DROP CONSTRAINT entry_shape_check,
    ADD CONSTRAINT entry_shape_check CHECK (CASE field
        WHEN 'name' THEN person IS NULL AND CASE
            WHEN present THEN value IS NOT NULL AND value <> ''
            ELSE value IS NULL
        END
        WHEN 'description' THEN person IS NULL AND CASE
            WHEN present THEN value IS NOT NULL AND value <> ''
            ELSE value IS NULL
        END
        WHEN 'tag' THEN value IS NOT NULL AND value <> '' AND person IS NULL
        WHEN 'owner' THEN value IS NULL AND person IS NOT NULL AND present
        WHEN 'collaborator' THEN value IS NULL AND person IS NOT NULL
        WHEN 'deleted' THEN value IS NULL AND person IS NULL
        WHEN 'language' THEN value IS NOT NULL
            AND value ~ '^[a-z]{2,3}(-[A-Za-z0-9]{1,8})*$'
            AND person IS NULL AND present
        WHEN 'varied' THEN value IS NOT NULL
            AND value ~ '^[1-9][0-9]{0,17}$'
            AND person IS NULL AND present
        WHEN 'replaced' THEN value IS NOT NULL
            AND value ~ '^(instructions|few_shot|prompt|output|sampling|reasoning|passthrough|translations|toolset|model)=(sha256:[0-9a-f]{64})?$'
            AND person IS NULL AND present
        WHEN 'with' THEN value IS NOT NULL
            AND value ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            AND person IS NULL AND present
    END) NOT VALID;
