# API

The bench's HTTP edge, for scripts and for the portal's islands: JSON under `/api/`, served by FastAPI on uvicorn,
validated and described by pydantic models (`src/chatddx/api/schemas.py`). The OpenAPI document is at
`/api/openapi.json`, and every route, request and response can be read and tried at `/api/docs` (Swagger UI); both are
public. The surface is stamped in `docs/surfaces/api.md`.

## Principles

- **A thin edge over the bench.** Each request opens its own autocommit Postgres connection (no pool,
  `src/chatddx/api/state.py:connection`), finds the person by their session, and holds a `Bench` for them
  (`src/chatddx/api/people.py:bench`). What a person sees and may do is the bench's to say; a route translates between
  its schemas and bench calls. Something another person holds, and the person doesn't see, isn't found.
- **Sessions.** `POST /api/session` answers a token and sets it as the `__Host-chatddx-session` cookie: Secure,
  HttpOnly, SameSite=Lax, for `settings.SESSION_TTL`. Every route but signing in needs the session, as a bearer token or
  the cookie. A cookie's unsafe requests, and every sign-in, must come from this site's pages
  (`src/chatddx/api/people.py:same_origin`, by `Sec-Fetch-Site`, else `Origin`, and one saying neither, as a script's,
  passes); a bearer's needn't. Sessions are rows in the database, so every process serving it knows them.

- **Strict schemas.** A request with a field the API doesn't know is a 422. A component is written as its JSON, `kind`
  included, as `GET /api/components/{digest}` gives its `body`; `GET /api/kinds` gives each kind's JSON Schema. Checking
  a component or a recipe, picking, trying a scorer and what a judge is asked are POSTs that write nothing.
- **One error shape.** Every error is an `Error`, `{"detail", "code"}`: a bench exception by
  `src/chatddx/api/app.py:STATUSES`, an HTTP status by `src/chatddx/api/app.py:CODES`, a request that doesn't validate
  as `unprocessable` with where. What a request's body or query names that is missing is a 422, what its path names a
  404 (`src/chatddx/api/state.py:refused`).

  | Status | Code                                | When                                                              |
  | ------ | ----------------------------------- | ----------------------------------------------------------------- |
  | 401    | `unauthenticated`                   | no session, or one that has ended                                 |
  | 403    | `cross_site`                        | a cookie's unsafe request from another site                       |
  | 404    | `not_found`                         | nothing the person sees by that path                              |
  | 405    | `not_allowed`                       | a method the path doesn't take                                    |
  | 409    | `ambiguous`, `conflict`, `moved_on` | a name for several, a clash with what holds, a head moved on from |
  | 422    | `refused`, `unprocessable`          | the bench or the gate refuses it; it doesn't validate             |
  | 429    | `over_quota`                        | a day's runs or typed cases, a run's items                        |
  | 500    | `error`                             | anything else, raw                                                |

- **Writes name what they saw.** What makes a thread or a family answers 201 with its `Location`. An edit names the head
  it was made on: one that changes nothing is a 200, one on a head the thread has moved on from a 409.
- **Runs are queued.** Starting, resuming, running again and scoring answer 202 with `Location`: a job is queued for the
  person at the run's endpoint, and a worker sends it, finishes it and, unless `score` is false, scores it, whether
  anyone listens or not. A start is a run per language its cases are sent in, and leaves out the cases it can't send.
  Each person's queue is theirs to pause and stop (`/api/queue`).
- **Events are Server-Sent Events.** `GET /api/runs/{run}/events` tells the run's rows in the ledger, the last event of
  each row with the row's number as its `id`, so that `Last-Event-ID` resumes after it. While a job for the run is
  queued or under way, it goes on with what the worker says as it happens, without ids, heard through Postgres
  `LISTEN`/`NOTIFY`, and the rows as they land; a comment line keeps a quiet stream alive. `done` is the last event. The
  events' names and data are `src/chatddx/api/schemas.py:EVENTS`, in the OpenAPI document's components.
- **The OpenAPI document is kept.** `frontend/openapi.json` is what `chatddx openapi` prints, and the portal's islands
  are typed from it (openapi-typescript, openapi-fetch). `scripts/check.sh` fails while it is behind the code, and flags
  it changing without `docs/surfaces/api.md`, or the other way round.

## Sensitive

Vignettes, a run's items (their calls, turns and answers), a score's items (their judge calls), and the events that
stream deltas, tools and judge calls are sensitive. The API gives them to the signed-in person who sees them, with
`Cache-Control: no-store` (`src/chatddx/api/state.py:no_store`): a family's vignette, a run's and a score's items, a
scorer tried, and the events. A 500's detail is raw and may quote sensitive content (`src/chatddx/api/app.py:_raw`), and
so may a failed job's `why`, in a run's `job` and its `error` event. What is still to hold before real patient data is
in `agents/wip-clearance.md`.

## Flows

Against the sample World on a migrated database, served by `chatddx api` with `chatddx worker` and
`chatddx fake-engines` beside it, after `chatddx init-data alice` and `chatddx person password alice`. The examples run
in one shell, each on what the one before it set, with curl's `--json` (7.82 or later) and jq.

1. Signing in, and asking who that is:

   ```sh
   API=http://localhost:8000/api
   TOKEN=$(curl -s --json '{"login": "alice", "password": "…"}' $API/session | jq -r .token)
   AUTH="Authorization: Bearer $TOKEN"
   curl -s $API/me -H "$AUTH"
   ```

2. Writing a component of one's own, forking a configuration with it as a part, and looking at what it would send:

   ```sh
   CHUNK=$(curl -s $API/threads -H "$AUTH" --json '{"name": "terse", "language": "en", "component":
     {"kind": "chunk.instructions", "role": "system", "text": "You assist an emergency physician. Be terse."}}' |
     jq -r .head.digest)
   PLAN=$(curl -s "$API/threads?kind=configuration&name=plan&owner=archive" -H "$AUTH" | jq '.[0].id')
   CONFIGURATION=$(curl -s $API/threads/$PLAN/forks -H "$AUTH" \
     --json "{\"name\": \"plan-terse\", \"parts\": {\"instructions\": \"$CHUNK\"}}" | jq .id)
   curl -s $API/threads/$CONFIGURATION/variation -H "$AUTH" | jq '{label, model, findings, messages: .request.messages}'
   ```

3. Taking the archive's expectation of a case, which scoring grades against, then running the configuration on it and
   following the run until it is scored:

   ```sh
   FAMILY=$(curl -s "$API/families?tag=dutch" -H "$AUTH" | jq '.[0].id')
   SCHEMA=$(curl -s $API/families/$FAMILY -H "$AUTH" | jq -r '.cases[0].expectations[0].expectation_schema')
   curl -s $API/takes -H "$AUTH" --json "{\"families\": [$FAMILY], \"expectation_schema\": \"$SCHEMA\"}"
   RUN=$(curl -s $API/runs -H "$AUTH" --json "{\"configuration\": $CONFIGURATION, \"families\": [$FAMILY]}" |
     jq -r '.runs[0].run')
   curl -sN $API/runs/$RUN/events -H "$AUTH"
   ```

4. Reading runs: the latest, one with its items and scores, and what an item answered:

   ```sh
   curl -s "$API/runs?limit=5" -H "$AUTH" | jq '.[] | {id, described, finished}'
   curl -s $API/runs/$RUN -H "$AUTH" | jq '{items, scores: [.scores[] | {name, labels, means}]}'
   curl -s $API/runs/$RUN/items -H "$AUTH" | jq '.[0].answer'
   ```
