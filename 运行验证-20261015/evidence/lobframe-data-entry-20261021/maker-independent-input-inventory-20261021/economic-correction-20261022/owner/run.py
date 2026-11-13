"""One offline unit: synthetic checks then sealed single formal replay. No network imports."""
import os,sys,time,signal,resource,json,gzip,csv,calendar,bisect,heapq,traceback
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from decimal import Decimal
OUT=Path(__file__).resolve().parent
UNIT=OUT.parent.parent
BASE=UNIT.parent
BOOT=time.monotonic();CPU=0.0
DEADLINE=calendar.timegm((2026,10,22,13,8,23))
from core import Engine,Order,Trade,D,ZERO,T,quantity,policy_pause,decimal_int,compare_paths
from inputs import sha,day0,load_quotes,load_trades,score_at
SOURCES=('core.py','inputs.py','run.py','tests.py','spec.json')
def utc():return datetime.now(timezone.utc).isoformat()
def save(name,x):
 with (OUT/name).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=True,allow_nan=False);f.write('\n')
def disk():return sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
class Budget:
 def __init__(self,phase):
  self.phase=phase;self.start=time.monotonic();self.cpu=time.process_time();self.peak=0
  self.prior=sum(json.loads(p.read_text()).get('CPU_seconds',0) for p in OUT.glob('resource-*.json'))
  rem=390-self.prior
  if rem<=0:raise TimeoutError('Owner CPU exhausted')
  resource.setrlimit(resource.RLIMIT_CPU,(max(1,int(rem)),max(2,int(rem)+1)))
  signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,1,1)
  signal.signal(signal.SIGXCPU,self.cpu_exceeded)
  self.guard()
 def cpu_exceeded(self,*args):raise TimeoutError('RLIMIT_CPU')
 def guard(self,*args):
  rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;self.peak=max(self.peak,rss)
  if time.time()>=DEADLINE:raise TimeoutError('Active deadline')
  if self.prior+time.process_time()-CPU>=390:raise TimeoutError('Cumulative Owner CPU390')
  if rss>536870912:raise MemoryError('512MiB RSS')
  if disk()>67108864:raise OSError('64MiB output cap')
 def finish(self,status):
  signal.setitimer(signal.ITIMER_REAL,0)
  r={'phase':self.phase,'status':status,'utc':utc(),'pid':os.getpid(),'CPU_seconds':time.process_time()-CPU,'wall_seconds':time.monotonic()-BOOT,'prior_Owner_CPU_seconds':self.prior,'conservative_old_CPU_debit_seconds':150,'review_reserve_CPU_seconds':60,'peak_RSS_bytes':max(self.peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'owner_output_bytes_before_receipt':disk(),'threads':1,'network':0,'actual_model':'UNKNOWN','actual_effort':'UNKNOWN'}
  r['cumulative_Owner_CPU_seconds']=self.prior+r['CPU_seconds'];r['cumulative_debit_including_reserve']=150+r['cumulative_Owner_CPU_seconds']+60
  save(f'resource-{self.phase}-{time.time_ns()}.json',r)
class Ledger:
 fields=['t','event','policy','model','delay_ms','order_id','side','limit','quantity','leaves','ahead','order_state','submit','accepted','cancel_sent','cancel_at','cash','BTC','fees','reserved_cash','reserved_BTC','pending_buy_BTC','mid_reference','inventory_price_term','execution_price_term','attribution_fees','detail']
 def __init__(self,path):
  self.f=gzip.open(path,'wt',newline='');self.w=csv.writer(self.f);self.w.writerow(self.fields);self.rows=0
 def write(self,t,event,e,o,detail):
  rc,ri,rb=e.reservations()
  self.w.writerow([t,event,e.policy,e.model,e.delay//10000,o.ident if o else '',o.side if o else '',o.price if o else '',o.qty if o else '',o.leaves if o else '',o.ahead if o else '',o.state if o else '',o.submit if o else '',o.accepted if o else '',o.cancel_sent if o else '',o.cancel_at if o else '',e.cash,e.inv,e.fees,rc,ri,rb,e.m if e.m is not None else '',e.attr_inventory,e.attr_execution,e.attr_fees,json.dumps(detail,separators=(',',':'),ensure_ascii=True)])
  self.rows+=1
 def close(self):self.f.close()

def input_metadata():
 prep=UNIT/'next-validation-design'/'input-readonly-precheck'
 prior=json.loads((prep/'input-metadata-identities.json').read_text())
 for x in prior['metadata_files']:
  if sha(x['path'])!=x['sha256']:raise ValueError('Prior input metadata changed')
 ledger=[json.loads(s) for s in (UNIT/'execution-20261022'/'owner'/'GET-ledger.jsonl').read_text().splitlines()]
 receipt=json.loads((BASE/'execution-20261021'/'data-receipt.json').read_text())
 raw=[x for x in ledger if x['day'] in ('2026-05-01','2026-06-01') and x['offset_minutes']<=540]
 if len(raw)!=110:raise ValueError('Fixed110 raw identities')
 selected=[]
 for day in ('2026-05-01','2026-06-01'):
  x=next(x for x in receipt['files'] if x['date']==day);p=Path(x['path']);st=p.stat()
  selected.append({'date':day,'path':str(p),'old_compressed_sha256':x['compressed_sha256'],'old_rows':x['rows'],'stat_size':st.st_size,'stat_mtime_ns':st.st_mtime_ns})
 return {'metadata':prior['metadata_files'],'raw':[{k:x[k] for k in ('day','path','sha256','offset_minutes')} for x in raw],'BBO':selected,'prior_QC_completion_sha256':sha(prep/'completion-receipt.json'),'prior_QC_summary_sha256':sha(prep/'summary.json')}

def prepare(budget):
 import tests
 result=tests.run()
 if not all(x['pass'] for x in result):raise AssertionError('Synthetic failure')
 save('synthetic-receipt.json',{'utc':utc(),'executable':sys.executable,'version':sys.version,'results':result,'count':len(result),'real_economic_input_used':False,'source_hashes':{n:sha(OUT/n) for n in SOURCES}})
 identities=input_metadata()
 spec=json.loads((OUT/'spec.json').read_text())
 for name,digest in spec['plans'].items():
  if sha(UNIT/'next-validation-design'/name)!=digest:raise ValueError('Plan identity')
 if sys.executable!=spec['runtime_executable'] or not sys.version.startswith(spec['runtime_version_prefix']):raise ValueError('Wrong actual runtime')
 save('preparation-seal.json',{'utc':utc(),'status':'READY_FOR_STATIC_REVIEW_NOT_FORMAL','source_hashes':{n:sha(OUT/n) for n in SOURCES},'runtime_executable':sys.executable,'runtime_version':sys.version,'authorization_sha256':sha(OUT.parent/'root'/'authorization.json'),'inputs':identities,'synthetic_receipt_sha256':sha(OUT/'synthetic-receipt.json')})
 return {'status':'READY_FOR_STATIC_REVIEW_NOT_FORMAL','synthetic_count':len(result)}

def formal(budget):
 seal=json.loads((OUT/'preparation-seal.json').read_text());release=json.loads((OUT.parent/'root'/'formal-release.json').read_text())
 if release.get('status')!='RELEASED_ONE_FORMAL_ECONOMIC_UNIT' or release.get('preparation_seal_sha256')!=sha(OUT/'preparation-seal.json'):raise PermissionError('Root release missing/mismatch')
 if sys.executable!=seal['runtime_executable'] or sys.version!=seal['runtime_version']:raise ValueError('Runtime identity drift')
 for n,h in seal['source_hashes'].items():
  if sha(OUT/n)!=h:raise ValueError('Frozen source drift')
 if sha(OUT.parent/'root'/'authorization.json')!=seal['authorization_sha256']:raise ValueError('Authorization drift')
 current=input_metadata()
 if current!=seal['inputs']:raise ValueError('Input metadata/stat drift vs frozen seal')
 for m in seal['inputs']['metadata']:
  if sha(m['path'])!=m['sha256']:raise ValueError('Input metadata hash drift')
 allresults=[]
 for day,expected in (('2026-05-01',5761),('2026-06-01',9318)):
  start=day0(day);trades=load_trades([r for r in seal['inputs']['raw'] if r['day']==day],start,budget)
  if len(trades)!=expected:raise ValueError('Trade prefix count drift')
  quotes=load_quotes(next(i for i in seal['inputs']['BBO'] if i['date']==day),start,budget)
  simulate_day(day,start,trades,quotes,budget,allresults)
  del quotes,trades
 comparisons=[]
 for day in ('2026-05-01','2026-06-01'):
  for model in ('E','X'):
   for ms in (100,500):
    f=next(r for r in allresults if r['day']==day and r['policy']=='F' and r['model']==model and r['delay_ms']==ms)
    h=next(r for r in allresults if r['day']==day and r['policy']=='H' and r['model']==model and r['delay_ms']==ms)
    comparisons.append(compare_paths(day,model,ms,f,h))
 passed=all(x['status']=='MODEL_CONDITIONAL_CELL_PASS' for x in comparisons)
 cashfail=any(x['status']=='CASH_NECESSARY_CONDITION_NOT_PASSED' for x in comparisons)
 cashunknown=any(not x['complete_cash_comparison'] for x in comparisons)
 riskunknown=any(not x['risk_complete_both'] for x in comparisons)
 status='IN_SAMPLE_MODEL_CONDITIONAL_ECONOMIC_CANDIDATE_ONLY' if passed else 'FIXED_COMBINATION_CASH_NECESSARY_CONDITIONS_NOT_PASSED' if cashfail else 'UNKNOWN_NOT_PROMOTED'
 result={'status':status,'utc':utc(),'comparisons':comparisons,'has_execution_cash_unknown':cashunknown,'has_risk_unknown':riskunknown,'path_results':allresults,'old_D_unchanged':True,'no_personal_fill_profit_capacity_claim':True,'unknown_external_costs_not_true_zero':True,'formal_attempts':1,'actual_model':'UNKNOWN','actual_effort':'UNKNOWN'}
 save('result.json',result);return {'status':status,'comparisons':comparisons}

def simulate_day(day,start,trades,quotes,budget,allresults):
 firstj=next((j for j in range(len(quotes.cap)) if quotes.cap[j]<start+5*T and quotes.src[j]*10<quotes.cap[j] and not quotes.bad[j]),None)
 if firstj is None:raise ValueError('No initial complete BBO observed before first decision; no window shift')
 firstbook=quotes.book(firstj)
 p0=(decimal_int(firstbook[0])+decimal_int(firstbook[2]))/2;q=quantity(p0)
 if q<=0:raise ValueError('q rounds0')
 ledger=Ledger(OUT/(day+'-ledger.csv.gz'))
 es=[Engine(p,m,d,q,quotes,ledger) for m in ('E','X') for d in (T//10,T//2) for p in ('F','H')]
 caps=[x.cap for x in trades];prefix=[];mx=-1
 for tr in trades:mx=max(mx,tr.src);prefix.append(mx)
 def maxsrc(t):
  j=bisect.bisect_left(caps,t);return prefix[j-1] if j else -1
 ti=bisect.bisect_left(caps,start+5*T);grid=5;cancelled=False;terminal=quotes.terminal(start+32451*T,start+32452*T)
 if terminal is None:raise ValueError('No fixed terminal reference')
 termtime,termref=terminal;done=False;steps=0
 try:
  for e in es:e.log(start+5*T,'initial',p0=str(p0),q=str(q),unit_assumption='BTC')
  while not done:
   ttrade=caps[ti] if ti<len(caps) else 2**63-1
   tgrid=start+grid*T if grid<=32449 else 2**63-1
   ttask=min((e.tasks[0][0] for e in es if e.tasks),default=2**63-1)
   tcancel=start+32450*T if not cancelled else 2**63-1
   t=min(ttrade,tgrid,ttask,tcancel,termtime)
   if t>termtime:raise ArithmeticError('Timeline surpassed terminal')
   # Common external print block first; same-clock decisions still use strict capture<t.
   if t==ttrade:
    batch=[]
    while ti<len(caps) and caps[ti]==t:batch.append(trades[ti]);ti+=1
    for e in es:e.prints(t,batch)
   for e in es:
    if e.tasks and e.tasks[0][0]==t:e.process_tasks(t,maxsrc(t))
   if t==tgrid:
    sign,safety,reason=score_at(t,trades,caps);f,h=policy_pause(day,grid,sign)
    for e in es:e.decision(t,f if e.policy=='F' else h,maxsrc(t),safety)
    grid+=1
   if t==tcancel:
    for e in es:e.all_cancel(t)
    cancelled=True
   if t==termtime:
    for e in es:e.terminal(t,termref)
    done=True
   steps+=1
   if steps%1000==0:budget.guard()
  results=[]
  for e in es:
   r=e.result();r['day']=day;r['terminal_time_capture_ticks']=termtime;r['ledger_file']=day+'-ledger.csv.gz';results.append(r);allresults.append(r)
  save(day+'-summary.json',{'date':day,'p0':str(p0),'q_BTC':str(q),'trade_prefix_count':len(trades),'BBO':quotes.meta,'terminal_capture_ticks':termtime,'terminal_reference_original_row':termref[0],'results':results,'ledger_rows':ledger.rows})
  print(json.dumps({'event':'day_complete','day':day,'paths':len(results),'ledger_rows':ledger.rows,'CPU_seconds':time.process_time()-CPU}),flush=True)
 finally:ledger.close()

def main():
 phase=sys.argv[1] if len(sys.argv)>1 else ''
 if phase not in ('prepare','formal'):raise ValueError('Explicitprepare/formal required')
 if (OUT/'first-stop.json').exists():raise RuntimeError('Existing terminalSTOP; no retry')
 if phase=='formal':
  # Atomic marker before any formal checks/guard construction: failures cannot be retried.
  save('formal-started.json',{'utc':utc(),'pid':os.getpid(),'executable':sys.executable,'version':sys.version,'argv':sys.argv,'source_hashes':{n:sha(OUT/n) for n in SOURCES}})
 budget=None;status='FAILED_STOP'
 try:
  budget=Budget(phase);ans=prepare(budget) if phase=='prepare' else formal(budget);status=ans['status'];print(json.dumps(ans),flush=True)
  save(phase+'-completion.json',{'utc':utc(),'status':status,'pid':os.getpid(),'exit_code':0,'actual_model':'UNKNOWN','actual_effort':'UNKNOWN'})
 except BaseException as exc:
  if phase=='formal' and not (OUT/'first-stop.json').exists():save('first-stop.json',{'utc':utc(),'status':'FORMAL_FAILED_STOP_NO_RETRY','type':type(exc).__name__,'message':str(exc),'pid':os.getpid()})
  else:
   if phase=='prepare':save('prepare-failure-'+str(time.time_ns())+'.json',{'utc':utc(),'type':type(exc).__name__,'message':str(exc)})
  traceback.print_exc();raise
 finally:
  if budget:budget.finish(status)
if __name__=='__main__':main()
