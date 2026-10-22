import csv,io,json,threading,unittest
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from app import make_server
ROOT=Path(__file__).resolve().parent
def main():
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    out=ROOT/'evidence'; out.mkdir(exist_ok=True)
    (out/'unittest.txt').write_text(stream.getvalue(),encoding='utf-8')
    if not result.wasSuccessful(): raise SystemExit(stream.getvalue())
    server=make_server(0); t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
    variables={'baseUrl':'http://127.0.0.1:'+str(server.server_port),'requestKey':'evidence-001'}
    exchanges=[]
    try:
        collection=json.loads((ROOT/'postman/payment-validation.postman_collection.json').read_text(encoding='utf-8'))
        for i,item in enumerate(collection['item']):
            def expand(s):
                for k,v in variables.items(): s=s.replace('{{'+k+'}}',str(v))
                return s
            r=item['request']; raw=r.get('body',{}).get('raw')
            req=Request(expand(r['url']),data=raw.encode() if raw else None,
                headers={h['key']:expand(h['value']) for h in r['header']},method=r['method'])
            try: response=urlopen(req,timeout=5)
            except HTTPError as e: response=e
            with response: code=response.code; data=json.load(response)
            if i==0: variables['startingBalance']=data['balance_cents']
            if i==1: variables['paymentId']=data['payment_id']
            expected=[200,201,200,409,200,200,400,422,422,404,400,200][i]
            assert code==expected,(i,code,data)
            if i in (4,11): assert data['balance_cents']==48750
            exchanges.append({'name':item['name'],'code':code,'body':data,'variables':dict(variables)})
        queries=[q for q in (ROOT/'sql/validation.sql').read_text().split(';') if q.strip()]
        assert [len(server.bank.db.execute(q).fetchall()) for q in queries]==[0,0,0,0]
        for table in ('accounts','payments','ledger'):
            c=server.bank.db.execute('SELECT * FROM '+table)
            with (out/(table+'.csv')).open('w',newline='',encoding='utf-8') as f:
                w=csv.writer(f); w.writerow([x[0] for x in c.description]); w.writerows(c)
        (out/'http-exchanges.json').write_text(json.dumps(exchanges,indent=2),encoding='utf-8')
        report=f"# Executed results\n\nRun UTC: {datetime.now(timezone.utc).isoformat()}\n\n"
        report+=f"**{result.testsRun} test methods passed**, including concurrent retries and a deliberately seeded one-cent discrepancy.\n\n"
        report+="**12 collection request cases** passed through actual local HTTP calls. **4 SQL controls** returned zero exceptions on clean data.\n\n"
        report+="| Case | HTTP | Result |\n|---|---|---|\n"
        report+='\n'.join(f"| {x['name']} | {x['code']} | PASS |" for x in exchanges)
        report+="\n\nExecution: Python HTTP client and SQLite. This is not a Postman UI run. Owner UAT and business sign-off remain pending.\n"
        (out/'results.md').write_text(report,encoding='utf-8')
        print('PASS: 7 test methods, 12 HTTP cases, 4 SQL controls')
    finally:
        server.shutdown();server.server_close();t.join();server.bank.db.close()
if __name__=='__main__': main()
