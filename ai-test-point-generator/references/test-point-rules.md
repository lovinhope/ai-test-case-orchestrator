# Test-point rules

- P0: core changed behavior and blocker findings.
- P1: boundaries, exceptions, important combinations, and historical-defect regressions.
- P2: permissions, compatibility, environments, and low-frequency paths.
- Describe actor/data, trigger, and observable business outcome before implementation details.
- Deduplicate only when setup and observable result are materially the same; retain all evidence references.
- Every point has `point_id`, `commit_id`, priority, type, source, expected focus, and confirmation status.

## Systematic coverage method

Coverage is judged by the rules and risks covered, not by the number of points. First decompose the requirement, confirmed business rules, design/interface contract, historical defects, and verified code behavior into independently verifiable rules. For each applicable rule, identify and trace test points for:

- functional behavior: what the system should do;
- data behavior: inputs, outputs, formats, precision, required fields, and persistence;
- permissions: who can view, create, modify, approve, or execute, and who must be denied;
- states: allowed and forbidden operations in each relevant business state and transition;
- exception behavior: validation, failure, error presentation, and system recovery;
- constraints: time, amount, quantity, range, format, and cross-field/combination relationships;
- non-functional risks where evidence or scope supports them: performance, security, compatibility, auditability, idempotency, and reliability.

Every applicable rule must map to at least one test point. If a dimension is not applicable or evidence is unavailable, record the reason as `awaiting_confirmation` or `skipped`; do not silently omit it or invent a rule.

## Scenario-dimension checklist

For each function and rule, check the following dimensions before finalizing points:

- normal flow;
- empty value and required-field behavior;
- minimum, maximum, and both sides of each boundary;
- out-of-range values;
- valid and invalid formats;
- single record, multiple records, and large-volume data;
- duplicate submission and repeated operation;
- interruption, timeout, network/dependency failure;
- different roles and permission scopes;
- each relevant business state and precondition satisfied/not satisfied;
- consistency across save, query, update, delete, and reload where applicable;
- rollback, retry, and recovery after failure.

Do not create mechanical points for irrelevant dimensions. Use the risk and evidence to decide depth, but explicitly document why a high-risk dimension is out of scope.

## Test-design models

Use one or more models to expose omissions instead of relying on the happy path alone:

- equivalence classes for valid and invalid input/data partitions;
- boundary-value analysis for the limit, just inside, and just outside the limit;
- decision tables for combinations of conditions that change the outcome;
- state-transition analysis for approval, order, product, transaction, and other stateful flows;
- cause-effect analysis for multiple inputs leading to a result;
- scenario/end-to-end analysis for complete business journeys;
- orthogonal or pairwise/combination coverage to control combinatorial explosion while prioritizing high-risk combinations.

The selected model and the resulting point IDs should be visible in the point type, source, or coverage note when they materially affect coverage.

## Requirement-to-point traceability

Include a compact traceability matrix or equivalent section in `03-test-points.md` when a requirement has multiple rules or dimensions. At minimum, map each rule to point IDs and mark applicable coverage dimensions such as normal, exception, boundary, permission, data validation, and state. A rule covered only by a happy-path point requires an explicit gap assessment before confirmation.

## Risk-based depth

Increase coverage depth for areas with high business impact or high defect likelihood, especially:

- funds, trading, positions, and permissions;
- irreversible or difficult-to-recover data changes;
- complex condition combinations;
- recently modified code and changed interfaces;
- historical defects or repeated incident patterns;
- external interfaces, asynchronous jobs, retries, and timeouts;
- core workflows or changes affecting many users.

Use business impact multiplied by failure likelihood as the prioritization heuristic. Keep the priority consistent with the existing P0/P1/P2 definitions and explain significant prioritization decisions in the source or rationale.

## Reverse coverage review

Before setting the points for human confirmation, perform and record a reverse check:

- Does every decomposed requirement rule have at least one point?
- Does each condition have true and false outcomes where applicable?
- Does each boundary include inside, exact boundary, and outside cases where applicable?
- Does each role include allowed and denied behavior where applicable?
- Does each relevant state include allowed and forbidden operations?
- Is data correct after success, failure, retry, rollback, and reload where applicable?
- Are duplicate, concurrent, timeout, network failure, and retry risks considered?
- Are historical defects covered or explicitly documented as unavailable/not applicable?

Do not claim full coverage merely because normal, negative, or boundary labels exist; the point's actor/data, trigger, and observable business outcome must make the coverage executable and auditable.
