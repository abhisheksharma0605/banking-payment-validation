# API contract v1 — fictional internal transfers

Base URL: `http://127.0.0.1:8765`. All amounts are integer minor units (USD cents).
No authentication is implemented; this demo binds only to localhost.

`POST /payments` requires JSON with exactly `source_id`, `destination_id`, `amount_cents`,
`currency`, plus a nonblank `Idempotency-Key` header up to 100 characters.

```json
{"source_id":"A100","destination_id":"A200","amount_cents":1250,"currency":"USD"}
```

| Situation | HTTP | Business outcome |
|---|---:|---|
| First valid request | 201 | One posted payment, debit and credit together |
| Same key, identical payload | 200 | Original payment ID returned; no new debit |
| Same key, different valid payload | 409 | `idempotency_conflict`; no change |
| Missing/invalid key, JSON or fields | 400 | No posting |
| Missing account | 404 | `account_not_found`; no posting |
| Blocked account, same source/destination, unsupported currency | 422 | No posting |
| Amount exceeds available balance | 422 | `insufficient_funds`; no posting |

`GET /accounts/{id}` returns `id`, `currency`, `status`, `balance_cents`.
`GET /payments/{id}` returns posted payment details. Missing IDs return 404.

Amounts must be integers from 1 to 100,000,000 inclusive. Booleans and decimals are rejected.
Only USD-to-USD active-account transfers are supported. Exact available balance is allowed.
Validation happens before deduplication; business rejections do not reserve the request key.
Successful keys persist for the lifetime of this in-memory demo. Production retention and
cross-process guarantees would require a separately agreed design.

## Why this is not ACH

This posts an internal transfer immediately. External ACH processing would require separate
submission, clearing, return and settlement states and agreed network rules; those are outside
this exercise. Do not describe this demo as ACH certification or ACH production experience.
