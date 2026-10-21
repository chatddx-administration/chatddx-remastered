-- Dependency: src/chatddx/catalog/families.py: family_of and _holder look a source's
-- bindings up by the vignette's id (binding_source) and by its content.
CREATE INDEX binding_content ON catalog.binding (source, fingerprint);
