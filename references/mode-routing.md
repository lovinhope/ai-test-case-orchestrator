# Mode routing

Use one or more modes. Do not force a source into a richer mode than its evidence supports.

| Mode | Recognize | Extract | Required output focus |
|---|---|---|---|
| requirement | PRD, story, rule, review report | actors, rules, states, acceptance criteria | happy path, negative, boundary, exception, combination |
| openapi | OpenAPI/Swagger JSON or YAML | path, method, parameters, required fields, enum, schema, response, security | contract, input, authorization, idempotency, error response |
| source_code | repository path, diff, commit, source files | entry point, branches, exceptions, dependencies, persistence | branch, failure, transaction, consistency, compatibility |
| historical_defect | defect record or knowledge-base evidence | symptom, trigger, root cause, fix, prior regression | traceable regression |
| business_profile | anonymized frequency, path, failure, concurrency aggregates | high-frequency path, unusual combination, error distribution | supplemental realistic scenario |

For requirement + OpenAPI or source code, compare contracts and mark mismatches `awaiting_confirmation`. For profile-only input, generate no requirement truth claims.
