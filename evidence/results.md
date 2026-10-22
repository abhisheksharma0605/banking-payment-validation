# Executed results

Run UTC: 2026-10-22T19:39:18.532893+00:00

**7 test methods passed**, including concurrent retries and a deliberately seeded one-cent discrepancy.

**12 collection request cases** passed through actual local HTTP calls. **4 SQL controls** returned zero exceptions on clean data.

| Case | HTTP | Result |
|---|---|---|
| 01 Read starting balance | 200 | PASS |
| 02 Create transfer | 201 | PASS |
| 03 Retry same instruction | 200 | PASS |
| 04 Reject changed amount | 409 | PASS |
| 05 Confirm one debit | 200 | PASS |
| 06 Inspect stored payment | 200 | PASS |
| 07 Zero amount | 400 | PASS |
| 08 Insufficient funds | 422 | PASS |
| 09 Blocked account | 422 | PASS |
| 10 Missing account | 404 | PASS |
| 11 Missing request key | 400 | PASS |
| 12 Verify final balance | 200 | PASS |

Execution: Python HTTP client and SQLite. This is not a Postman UI run. Owner UAT and business sign-off remain pending.
