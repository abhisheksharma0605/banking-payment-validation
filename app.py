"""A small synthetic internal-transfer API, not an ACH or production banking API."""
import json
import sqlite3
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class Bank:
    def __init__(self):
        self.lock = threading.Lock()
        self.db = sqlite3.connect(':memory:', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE accounts(id TEXT PRIMARY KEY, currency TEXT NOT NULL,
              status TEXT NOT NULL, opening_cents INTEGER NOT NULL,
              balance_cents INTEGER NOT NULL CHECK(balance_cents >= 0));
            CREATE TABLE payments(id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
              request_json TEXT NOT NULL, source_id TEXT REFERENCES accounts(id),
              destination_id TEXT REFERENCES accounts(id), amount_cents INTEGER NOT NULL,
              currency TEXT NOT NULL, status TEXT NOT NULL);
            CREATE TABLE ledger(id INTEGER PRIMARY KEY, payment_id TEXT REFERENCES payments(id),
              account_id TEXT REFERENCES accounts(id), signed_cents INTEGER NOT NULL);
            INSERT INTO accounts VALUES
              ('A100','USD','active',50000,50000), ('A200','USD','active',10000,10000),
              ('A300','USD','blocked',25000,25000), ('A400','CAD','active',40000,40000);
        """)

    def transfer(self, body, key):
        if not isinstance(key, str) or not key.strip() or len(key) > 100:
            return 400, {'error': 'invalid_idempotency_key'}
        fields = {'source_id', 'destination_id', 'amount_cents', 'currency'}
        if not isinstance(body, dict) or set(body) != fields:
            return 400, {'error': 'invalid_fields'}
        if (type(body['amount_cents']) is not int or not 0 < body['amount_cents'] <= 100000000
                or any(not isinstance(body[k], str) for k in fields - {'amount_cents'})):
            return 400, {'error': 'invalid_fields'}
        fingerprint = json.dumps(body, sort_keys=True)
        with self.lock:
            prior = self.db.execute('SELECT * FROM payments WHERE request_key=?', (key,)).fetchone()
            if prior:
                if prior['request_json'] != fingerprint:
                    return 409, {'error': 'idempotency_conflict'}
                return 200, {'payment_id': prior['id'], 'status': 'posted', 'replayed': True}
            src = self.db.execute('SELECT * FROM accounts WHERE id=?', (body['source_id'],)).fetchone()
            dst = self.db.execute('SELECT * FROM accounts WHERE id=?', (body['destination_id'],)).fetchone()
            if not src or not dst:
                return 404, {'error': 'account_not_found'}
            if src['id'] == dst['id']:
                return 422, {'error': 'same_account'}
            if src['status'] != 'active' or dst['status'] != 'active':
                return 422, {'error': 'account_blocked'}
            if body['currency'] != 'USD' or src['currency'] != 'USD' or dst['currency'] != 'USD':
                return 422, {'error': 'unsupported_currency'}
            amount = body['amount_cents']
            if src['balance_cents'] < amount:
                return 422, {'error': 'insufficient_funds'}
            pid = 'PAY-' + uuid.uuid4().hex[:16]
            with self.db:
                self.db.execute('INSERT INTO payments VALUES(?,?,?,?,?,?,?,?)',
                    (pid, key, fingerprint, src['id'], dst['id'], amount, 'USD', 'posted'))
                self.db.execute('UPDATE accounts SET balance_cents=balance_cents-? WHERE id=?', (amount, src['id']))
                self.db.execute('UPDATE accounts SET balance_cents=balance_cents+? WHERE id=?', (amount, dst['id']))
                self.db.executemany('INSERT INTO ledger(payment_id,account_id,signed_cents) VALUES(?,?,?)',
                    [(pid, src['id'], -amount), (pid, dst['id'], amount)])
            return 201, {'payment_id': pid, 'status': 'posted', 'replayed': False}


def make_server(port=8765, bank=None):
    bank = bank or Bank()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send_json(self, status, body):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlparse(self.path).path
            with bank.lock:
                if path.startswith('/accounts/'):
                    row = bank.db.execute('SELECT id,currency,status,balance_cents FROM accounts WHERE id=?',
                                          (path[len('/accounts/'):],)).fetchone()
                    return self.send_json(200, dict(row)) if row else self.send_json(404, {'error': 'account_not_found'})
                if path.startswith('/payments/'):
                    row = bank.db.execute('SELECT id,source_id,destination_id,amount_cents,currency,status FROM payments WHERE id=?',
                                          (path[len('/payments/'):],)).fetchone()
                    return self.send_json(200, dict(row)) if row else self.send_json(404, {'error': 'payment_not_found'})
            self.send_json(404, {'error': 'route_not_found'})

        def do_POST(self):
            if urlparse(self.path).path != '/payments':
                return self.send_json(404, {'error': 'route_not_found'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 4096:
                    return self.send_json(400, {'error': 'invalid_body_size'})
                body = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeDecodeError):
                return self.send_json(400, {'error': 'invalid_json'})
            status, payload = bank.transfer(body, self.headers.get('Idempotency-Key'))
            self.send_json(status, payload)

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.bank = bank
    return server


if __name__ == '__main__':
    server = make_server()
    print('Synthetic payment API: http://127.0.0.1:8765 — Ctrl+C to stop', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
