-- SQLite dialect. Each control returns exceptions. A clean run returns zero rows.
-- Control 1: an accepted request key must identify only one payment.
SELECT request_key, COUNT(*) AS copies FROM payments
GROUP BY request_key HAVING COUNT(*) > 1;

-- Control 2: each payment needs exactly two balanced entries.
SELECT p.id, COUNT(l.id) AS entry_count, COALESCE(SUM(l.signed_cents),0) AS net_cents
FROM payments p LEFT JOIN ledger l ON l.payment_id=p.id
GROUP BY p.id HAVING COUNT(l.id) <> 2 OR SUM(l.signed_cents) <> 0;

-- Control 3: balance must equal opening balance plus signed ledger movement.
SELECT a.id, a.balance_cents, a.opening_cents + COALESCE(SUM(l.signed_cents),0) AS expected_cents
FROM accounts a LEFT JOIN ledger l ON l.account_id=a.id
GROUP BY a.id HAVING a.balance_cents <> a.opening_cents + COALESCE(SUM(l.signed_cents),0);

-- Control 4: the debit and credit must match the correct account AND amount.
SELECT p.id FROM payments p
WHERE (SELECT COUNT(*) FROM ledger l WHERE l.payment_id=p.id
       AND l.account_id=p.source_id AND l.signed_cents=-p.amount_cents) <> 1
   OR (SELECT COUNT(*) FROM ledger l WHERE l.payment_id=p.id
       AND l.account_id=p.destination_id AND l.signed_cents=p.amount_cents) <> 1;
