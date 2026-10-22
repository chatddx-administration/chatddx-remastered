# Identity

Who a :Person is, and what they own and see. A person has a :Login, a name and roles, which nothing checks yet
(`src/chatddx/identity/identity.py:Person`); `owns`, `collaborates` and `sees` decide over what is said to be owned
(`src/chatddx/identity/identity.py:Owned`); and passwords are hashed with argon2 and session tokens kept as a digest
(`src/chatddx/identity/identity.py:hash_password`, `src/chatddx/identity/identity.py:token_digest`). It is plain Python
and reads and writes nothing: the store keeps people, passwords and sessions (`src/chatddx/store/people.py:People`), and
the catalog says who owns and collaborates on a subject (`src/chatddx/catalog/model.py:About`).
