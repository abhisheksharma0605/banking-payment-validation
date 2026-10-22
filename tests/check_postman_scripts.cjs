const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const c=JSON.parse(fs.readFileSync(path.join(root,'postman/payment-validation.postman_collection.json'),'utf8'));
const exchanges=JSON.parse(fs.readFileSync(path.join(root,'evidence/http-exchanges.json'),'utf8'));
let count=0;
c.item.forEach((item,i)=>{
 const e=exchanges[i],v={...e.variables};
 const pm={response:{json:()=>e.body,to:{have:{status:n=>assert.strictEqual(e.code,n)}}},
 collectionVariables:{get:k=>v[k],set:(k,x)=>{v[k]=x}},variables:{replaceIn:()=> 'mock-guid'},
 expect:x=>({to:{eql:y=>assert.deepStrictEqual(x,y)}}),test:(name,f)=>{f();count++}};
 for(const event of item.event) vm.runInNewContext(event.script.exec.join('\n'),{pm});
});
const result={assertions_passed:count,scope:'JavaScript harness against recorded HTTP responses; not Postman UI'};
fs.writeFileSync(path.join(root,'evidence/postman-script-check.json'),JSON.stringify(result,null,2));
console.log(result);
