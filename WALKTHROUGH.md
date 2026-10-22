# Learn it, run it, explain it

## 1. Start with the business question (5 minutes)

Why might a customer submit twice? A timeout or a second click. Should two network requests
always mean two payments? No. Explain that distinction before reading the code.

## 2. Read a request (10 minutes)

Open the Postman collection. `amount_cents: 1250` means $12.50. The request key is a reference
for this instruction, not a customer password. `201` means created; the replay's `200` returns
the existing result. Describe why `409` is appropriate for a changed amount with the same key.

## 3. Follow the SQL (15 minutes)

Read control 3 in `sql/validation.sql`. A LEFT JOIN preserves accounts with no ledger rows.
SUM calculates net movement; COALESCE turns no movement into zero. HAVING filters grouped
results to exceptions. Predict A100's balance after a single $12.50 transfer, then run the tests.

## 4. Make one change yourself (15 minutes)

Add a test that transfers $1.00 from A200 to A100 using a new key. Predict both balances first.
Run it. Record what changed and why. Do not change recorded expected results just to make a failing test pass.

## 5. Interview explanation (after completing the steps)

“I used an AI-assisted banking simulation to practise API and SQL validation. I checked that a
retry returned the same payment ID without a second debit, and used a ledger reconciliation
query to detect an intentionally seeded discrepancy. This was a personal practice project,
not work delivered to a bank.” Adapt this to what you personally completed.

## Your evidence log — initially uncompleted

| Task | My observation | Date |
|---|---|---|
| Explain the request key in my own words | Pending | — |
| Run the Postman collection myself | Pending | — |
| Explain LEFT JOIN / SUM / HAVING | Pending | — |
| Add and verify my own test | Pending | — |
