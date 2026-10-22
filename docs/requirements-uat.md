# Requirements and UAT design

All roles and decisions below belong to the simulated project. No business sign-off is claimed.

| ID | Requirement / acceptance criterion | Test evidence |
|---|---|---|
| PAY-01 | Given two active USD accounts, when a valid transfer is submitted, exactly one payment and two matching ledger entries exist | `test_success_and_replay_post_only_once`; SQL controls 2–4 |
| PAY-02 | Given a completed request, when identical content and key are retried, the same payment ID returns and balances stay unchanged | `test_success_and_replay_post_only_once`; `test_concurrent_retries_create_one_payment` |
| PAY-03 | Given a used key, when the amount changes, return 409 with no additional posting | `test_conflicting_payload_rejected` |
| PAY-04 | Given insufficient funds, blocked/missing accounts or invalid amount, reject without any persisted posting | `test_invalid_requests_leave_no_posting` |
| PAY-05 | An amount exactly equal to available balance is valid | `test_exact_available_balance_is_allowed` |
| PAY-06 | Reject malformed input or missing idempotency key | `test_missing_key_and_malformed_json` |
| PAY-07 | Reconciliation must detect a balance inconsistent with the ledger | `test_reconciliation_detects_a_seeded_imbalance` |

## Manual UAT procedure (owner execution pending)

1. Start a fresh server. GET A100 and A200: expect 50,000 and 10,000 cents.
2. POST the 1,250-cent request using key `uat-001`: expect 201.
3. Retry unchanged: expect 200 and the same payment ID.
4. GET both accounts: expect 48,750 and 11,250 cents, not two transfers.
5. Change the amount to 1,300 while retaining the key: expect 409.
6. Capture actual responses in a local practice log. Never mark business approval from automation alone.

Release gates: all functional controls pass, no unresolved high-impact defects, and business owner
acceptance of the demo scope. Only the first gate can be established by the automated suite.
