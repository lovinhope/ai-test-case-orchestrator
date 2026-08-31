# Test-database data contract

Use this contract when a generated test case requires concrete records in a test database. This capability creates test data only for the current test run; it is not a general database administration interface.

## Configuration and environment safety

- Resolve the database configuration from the local project/test configuration or an explicitly configured `TEST_DB_CONFIG_PATH`. Never ask the requester to paste credentials into chat and never print credentials, connection URLs containing secrets, or full connection errors.
- Support the existing Lowrisk data-mock adapter when the requested scenario matches its asset and table rules. Reuse its schema mappings and reference resolvers instead of duplicating SQL.
- Before connecting, verify an explicit non-production environment marker (`test`, `qa`, `staging`, or equivalent), host/database allowlist, and account scope. If the target cannot be proven non-production, stop with `test_database_unverified`; do not connect or write.
- Prefer a read-only connection for discovery. Use a write-capable connection only after the user has explicitly requested data creation for this test run.

## Data-generation workflow

1. Decide whether the case requires data, then derive the complete minimum dataset from the changed project code and call chain: actual entry point, tables/entities, joins, filters, caches, enums, statuses, dates, scope, and upstream/downstream records—not from the requirement text alone.
2. Query existing reference data first and reuse stable IDs where safe. Inspect schema, mapper/SQL, DTOs, configuration, fixtures, and reference tables to confirm field meaning and value semantics. Do not invent foreign keys, enum values, business states, product codes, stock types/statuses, or fields that are not present in verified project evidence.
3. Include every record required to reach the asserted branch and its control branch, including related order, position, valuation, page-query, permission, cache, or daily-snapshot data when those are read by the implementation. Prefer one shared dataset when cases have identical parameters and required state; document the case-to-dataset mapping instead of duplicating records.
4. Produce a data plan before writing: scenario, code path, tables/entities, fields, source of each value, required relationships/state transitions, uniqueness strategy, expected IDs, cleanup strategy, and linked case numbers.
5. Generate an idempotent, run-scoped dataset using a unique `run_id`/test tag. Keep inserts, updates, and required state transitions traceable to the case.
6. Execute writes in a transaction or an equivalent compensating-rollback boundary. Verify inserted rows and the required business state after writing.
7. Persist a non-secret manifest at `04-test-data-manifest.md` containing environment name, run id, created entity/table identifiers, verification results, cleanup command or procedure, and linked cases. Never persist passwords or tokens.
8. If code, schema, reference data, or environment verification fails, stop data creation, record the exact blocker and unresolved field/value, leave the dataset `待准备`/`test_data_pending`, and never claim that data exists.

## Required controls

- Do not use production data as test data without approved anonymization and an explicit safe-copy process.
- Do not perform broad `UPDATE`, `DELETE`, schema changes, permission changes, or unscoped writes.
- Do not delete pre-existing records. Cleanup may remove only records created by the current run and only when the manifest proves ownership.
- Respect foreign-key order, audit fields, tenant/product scope, and business workflows; direct database state changes must not bypass required setup APIs when the case depends on API behavior.
- Mask sensitive values in logs and artifacts.
- If the database adapter, schema, or environment is unavailable, generate a data plan or executable SQL draft for review, but do not report successful creation.

## Case linkage

Every case that uses generated data must reference the manifest and its own data-set identifier in `前置条件` and `来源及依据`. A case is not executable until its required data-set status is `verified`.
