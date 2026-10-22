import concurrent.futures
import json
from pathlib import Path
import sys
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import make_server

class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server(0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)
        self.body = dict(source_id='A100', destination_id='A200', amount_cents=1250, currency='USD')

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.server.bank.db.close()

    def request(self, body=None, key='test-1', path='/payments', method='POST', raw=None):
        data = raw if raw is not None else (json.dumps(body or self.body).encode() if method == 'POST' else None)
        headers = {'Content-Type': 'application/json'}
        if key is not None: headers['Idempotency-Key'] = key
        req = Request(self.base + path, data=data, method=method, headers=headers)
        try: response = urlopen(req, timeout=5)
        except HTTPError as error: response = error
        with response:
            return response.code, json.load(response)

    def balance(self):
        return self.request(path='/accounts/A100', method='GET')[1]['balance_cents']

    def test_success_and_replay_post_only_once(self):
        code, first = self.request(); self.assertEqual(code, 201)
        code, replay = self.request(); self.assertEqual(code, 200)
        self.assertEqual(first['payment_id'], replay['payment_id'])
        self.assertTrue(replay['replayed']); self.assertEqual(self.balance(), 48750)
        self.assertEqual(self.server.bank.db.execute('SELECT COUNT(*) FROM ledger').fetchone()[0], 2)

    def test_conflicting_payload_rejected(self):
        self.request()
        code, data = self.request({**self.body, 'amount_cents': 1300})
        self.assertEqual((code,data['error']), (409,'idempotency_conflict'))
        self.assertEqual(self.balance(),48750)

    def test_invalid_requests_leave_no_posting(self):
        cases = [(dict(amount_cents=0),400,'invalid_fields'),
                 (dict(amount_cents=-1),400,'invalid_fields'),
                 (dict(amount_cents=1.5),400,'invalid_fields'),
                 (dict(amount_cents=True),400,'invalid_fields'),
                 (dict(amount_cents=50001),422,'insufficient_funds'),
                 (dict(destination_id='A300'),422,'account_blocked'),
                 (dict(destination_id='A400'),422,'unsupported_currency'),
                 (dict(destination_id='UNKNOWN'),404,'account_not_found'),
                 (dict(destination_id='A100'),422,'same_account')]
        for changes, expected_code, expected_error in cases:
            with self.subTest(changes=changes):
                code, data = self.request({**self.body, **changes})
                self.assertEqual((code,data['error']),(expected_code,expected_error))
                self.assertEqual(self.balance(),50000)
        self.assertEqual(self.server.bank.db.execute('SELECT COUNT(*) FROM payments').fetchone()[0],0)

    def test_missing_key_and_malformed_json(self):
        self.assertEqual(self.request(key=None)[0],400)
        self.assertEqual(self.request(raw=b'{bad')[1]['error'],'invalid_json')
        self.assertEqual(self.request(raw=b'[]')[0],400)

    def test_exact_available_balance_is_allowed(self):
        self.assertEqual(self.request({**self.body,'amount_cents':50000})[0],201)
        self.assertEqual(self.balance(),0)

    def test_concurrent_retries_create_one_payment(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: self.request(), range(8)))
        self.assertEqual(sorted(code for code,_ in results),[200]*7+[201])
        self.assertEqual(len({data['payment_id'] for _,data in results}),1)
        self.assertEqual(self.balance(),48750)

    def test_reconciliation_detects_a_seeded_imbalance(self):
        self.request()
        sql = (Path(__file__).resolve().parents[1]/'sql/validation.sql').read_text()
        queries = [q for q in sql.split(';') if q.strip()]
        for query in queries: self.assertEqual(self.server.bank.db.execute(query).fetchall(),[])
        self.server.bank.db.execute("UPDATE accounts SET balance_cents=balance_cents-1 WHERE id='A100'")
        self.assertEqual(len(self.server.bank.db.execute(queries[2]).fetchall()),1)

if __name__ == '__main__': unittest.main()
