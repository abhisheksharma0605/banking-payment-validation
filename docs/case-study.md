# Case study: the customer clicks Pay twice

**Type:** independent, AI-assisted banking practice. **Business context:** fictional internal transfer.

## Problem and decision

A customer receives no immediate confirmation and retries. Treating each HTTP call as a new
business instruction could debit twice. The proposed rule separates a request attempt from a
payment: the same request key and payload identify the same payment.

The tradeoff is intentional: a customer who truly wants another identical transfer needs a new
key. Reusing a key with different payment details is a conflict, not a silent update.

## Analysis work represented by this project

The artifacts clarify validation order, document acceptance criteria, link them to test cases,
compare response IDs against ledger and balance changes, and define a release gate. The initial
artifacts and code were generated with Codex; owner review and practice are tracked separately.

## Investigation example: a one-cent discrepancy

The test suite deliberately subtracts one cent from A100 after a valid transfer, leaving its
ledger unchanged. The balance reconciliation flags A100 because stored balance no longer equals
opening balance plus ledger movement. This is a **seeded laboratory defect**, not a discovered
FIS incident. It shows why checking only an HTTP 201 is insufficient.

Suggested ticket: `LAB-01 — Stored account balance differs from ledger-derived balance`.
Severity: high within the simulation because displayed money is incorrect. Reproduction:
run `test_reconciliation_detects_a_seeded_imbalance`; expected discrepancy count changes from 0 to 1.
Root-cause hypothesis: a balance change bypassed ledger posting. Evidence supports the inconsistency;
it would not establish the cause of a real incident without further investigation.

## Results and limitations

See the generated evidence for actual run results. There is no claimed reduction in production
incidents, cost saving, transaction scale or employer outcome. The next useful extension is to add
a pending-to-posted workflow and define how retries behave before completion.
