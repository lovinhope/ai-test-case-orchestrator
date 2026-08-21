# Quality gates

The static validator blocks final delivery for missing P0 coverage, unmatched step/expected-result counts, missing source metadata, duplicate case titles, unconfirmed business rules, or missing regression references.

Metric gates:

| Condition | Gate |
|---|---|
| P0 coverage < 100% | block final cases |
| adoption rate >= 60% | pass |
| adoption rate >= 40% and < 60% | yellow: manual review required |
| adoption rate < 40% | red: stop the generation pipeline |

Execution effectiveness is `passed / executed`. Report `not_available` when execution data is absent; do not fabricate it.
