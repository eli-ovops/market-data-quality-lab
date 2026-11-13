"""Prepare synthetic checks, then ONE Root-sealed saved-label linkage; no market readers."""
import os,sys,csv,gzip,io,json,time,signal,resource,hashlib,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
from decimal import Decimal
from linkage_core import Cov,Batch,Metric,HEADER,integer,identity,evaluate_batch,T
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent/'root'
SOURCES=('linkage.py','linkage_core.py','fixtures.py')
PROTOCOL_SHA='76ef210b29e92307ad50ab67908a878a4eb6de8062a3fb26ae954b5d9b5beb0e'
METHOD_SHA='3d135b50da27e9d5b825fcd5b0d0996dc861877fd80459f461dcdd2201717088'
INVENTORY_SHA='555e27bcbaed27a453d04c3e8d7daa1e1aac6e60a97c5b37064ce1c6e6bc9d1d'
BOOT=time.monotonic();PHASE=None;guard=None

def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
 with (OUT/n).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False,default=str);f.write('\n')
def disk():return sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
def source_hashes():return {n:sha(OUT/n) for n in SOURCES}
class Guard:
 def __init__(self,phase):
  self.phase=phase;self.prior=sum(json.loads(p.read_text())['CPU_seconds'] for p in OUT.glob('resource-*.json'));self.deadline=datetime.fromisoformat(json.loads((ROOT/'protocol.json').read_text())['utc'])+timedelta(hours=2)
  remaining=210-self.prior
  if remaining<=0:raise TimeoutError('Cumulative Data CPU210')
  resource.setrlimit(resource.RLIMIT_CPU,(max(1,math.ceil(remaining)),max(2,math.ceil(remaining)+1)))
  signal.signal(signal.SIGALRM,self.check);signal.signal(signal.SIGXCPU,self.check);signal.setitimer(signal.ITIMER_REAL,1,1);self.check()
 def check(self,*a):
  if self.prior+time.process_time()>=209:raise TimeoutError('Cumulative Data CPU209 guard/210 cap')
  if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>268435456:raise MemoryError('RSS256MiB')
  if disk()>16777216:raise OSError('Output16MiB')
  if datetime.now(timezone.utc)>=self.deadline:raise TimeoutError('Protocol UTC plus2h deadline')
 def finish(self,status):
  signal.setitimer(signal.ITIMER_REAL,0)
  save('resource-'+self.phase+'-'+str(time.time_ns())+'.json',{'utc':utc(),'phase':self.phase,'status':status,'CPU_seconds':time.process_time(),'prior_Data_CPU_seconds':self.prior,'cumulative_Data_CPU_seconds':self.prior+time.process_time(),'Root_Reviewer_reserve_seconds':90,'wall_seconds':time.monotonic()-BOOT,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'output_bytes_before_receipt':disk(),'pid':os.getpid(),'threads':1,'network':0,'actual_model_effort_speed':'UNKNOWN'})
class HashRead:
 def __init__(self,f):self.f=f;self.h=hashlib.sha256();self.n=0
 def read(self,n=-1):
  b=self.f.read(n);self.h.update(b);self.n+=len(b);return b
 def tell(self):return self.f.tell()
def context():
 if sha(ROOT/'protocol.json')!=PROTOCOL_SHA or sha(ROOT/'固定匹配与覆盖方法.md')!=METHOD_SHA or sha(OUT/'input-sources.json')!=INVENTORY_SHA:raise ValueError('Fixed method/input inventory changed')
 inv=json.loads((OUT/'input-sources.json').read_text());proto=json.loads((ROOT/'protocol.json').read_text());runtime=inv['runtime']
 if sys.executable!=runtime['executable'] or sys.version!=runtime['actual_version']:raise ValueError('Actual Python runtime drift')
 small={}
 for src in inv['sources']:
  for n,h in [('manifest_path','manifest_sha256'),('summary_path','summary_sha256')]:
   if sha(src[n])!=src[h]:raise ValueError('Small input identity drift')
   small[src[n]]=src[h]
 for spec in inv['schema_sources']:
  if sha(spec['path'])!=spec['sha256']:raise ValueError('Schema source changed')
  small[spec['path']]=spec['sha256']
 return inv,proto,small

def prepare():
 inv,proto,small=context()
 from fixtures import run
 tests=run()
 if not all(t['pass'] for t in tests):raise AssertionError('Artificial fixture failure')
 save('synthetic-receipt.json',{'utc':utc(),'tests':tests,'count':len(tests),'all_pass':True,'real_input_bodies_opened':False,'runtime_executable':sys.executable,'runtime_version':sys.version,'source_hashes':source_hashes()})
 save('preparation-seal.json',{'utc':utc(),'status':'READY_FOR_STATIC_REVIEW_NOT_FORMAL','source_hashes':source_hashes(),'protocol_sha256':PROTOCOL_SHA,'method_sha256':METHOD_SHA,'input_inventory_sha256':INVENTORY_SHA,'small_input_hashes':small,'runtime_executable':sys.executable,'runtime_version':sys.version,'synthetic_receipt_sha256':sha(OUT/'synthetic-receipt.json'),'large_input_body_reads':0,'formal_linkage_runs':0})
 return {'status':'READY_FOR_STATIC_REVIEW_NOT_FORMAL','fixture_count':len(tests)}

def read_coverage(src):
 index={};dups=Counter();n=0
 with Path(src['path']).open('rb') as raw:
  h=HashRead(raw)
  with gzip.GzipFile(fileobj=h,mode='rb') as gz,io.TextIOWrapper(gz) as text:
   for n,line in enumerate(text,1):
    r=json.loads(line);c=Cov.from_row(r)
    if c.ident in index:index[c.ident]=False;dups[c.ident]+=1
    else:index[c.ident]=c
    if n%1024==0:guard.check()
 if h.h.hexdigest()!=src['sealed_sha256'] or h.n!=src['sealed_compressed_bytes'] or n!=src['sealed_data_rows_excluding_CSV_header_if_any']:raise ValueError('Coverage SHA/bytes/row drift')
 return index,{'path':src['path'],'day':src['day'],'kind':src['kind'],'sha256':h.h.hexdigest(),'bytes':h.n,'data_rows':n,'gzip_EOF_CRC':True,'duplicate_tradeID_keys':len(dups)}

def parse_batch(r,ix,n):
 detail=json.loads(r[ix['detail']]);kind=detail['fill_kind'];qty=Decimal(detail['qty']);price=Decimal(detail['fill_price']);limit=Decimal(r[ix['limit']])
 if not qty.is_finite() or qty<=0 or not price.is_finite() or price<=0 or not limit.is_finite() or limit<=0:raise ValueError('Invalid saved maker buy price/qty')
 refs=detail.get('trade_ids');ids=[];invalid=0
 if not isinstance(refs,list):invalid=1
 else:
  for x in refs:
   try:ids.append(identity(x))
   except ValueError:invalid+=1
 return Batch(n,integer(r[ix['t']]),kind,qty,price,limit,r[ix['accepted']],r[ix['cancel_at']],tuple(dict.fromkeys(ids)),invalid,len(ids)!=len(set(ids)),r[ix['order_id']])

def read_day_ledger(src,index,inv,cutoffs,audit):
 day=src['day'];start=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())*T
 paths={};cells={};prefix_metrics={};rows={};other={};fill_count={};n=0;reasons_witness={}
 for m in ('E','X'):
  for delay in (100,500):
   cells[(m,delay)]=Metric()
   for policy in ('F1','H1'):
    k=(m,delay,policy);paths[k]=Metric();prefix_metrics[k]=Metric();rows[k]={'rows':0,'first_t':None,'last_t':None,'rows_at_or_after_common_freeze':0};other[k]=Counter();fill_count[k]=0
 with Path(src['path']).open('rb') as raw:
  h=HashRead(raw)
  with gzip.GzipFile(fileobj=h,mode='rb') as gz,io.TextIOWrapper(gz,newline='') as text:
   reader=csv.reader(text);header=next(reader)
   if header!=HEADER:raise ValueError('Saved ledger header drift')
   ix={x:i for i,x in enumerate(header)}
   for n,r in enumerate(reader,1):
    if len(r)!=len(header):raise ValueError('Malformed ledger row')
    k=(r[ix['model']],integer(r[ix['delay_ms']]),r[ix['policy']]);meta=rows[k];t=integer(r[ix['t']]);cut=cutoffs[(day,k[0],k[1])]
    if meta['last_t'] is not None and t<meta['last_t']:raise ValueError('Path capture order drift')
    meta['rows']+=1;meta['first_t']=t if meta['first_t'] is None else meta['first_t'];meta['last_t']=t;meta['rows_at_or_after_common_freeze']+=bool(cut is not None and t>=cut)
    if r[ix['event']]=='fill':
     fill_count[k]+=1;detail=json.loads(r[ix['detail']]);kind=detail['fill_kind'];side=r[ix['side']]
     if side=='buy' and kind in ('equal','cross'):
      b=parse_batch(r,ix,n);e=evaluate_batch(b,index,start);paths[k].add(b,e);common=cut is None or t<cut
      if common:prefix_metrics[k].add(b,e);cells[k[:2]].add(b,e)
      reference_records=[]
      for rr in e['refs']:
       q=dict(rr);c=index.get(rr['tradeID'])
       q['transferred_loss_bp']=float(c.label['loss_bp']) if rr['transfer']=='ELIGIBLE' else None
       reference_records.append(q)
      record={'day':day,'model':k[0],'delay_ms':k[1],'policy':k[2],'ledger_row':n,'t':t,'virtual_order_id':b.order_id,'kind':kind,'BTC_qty':str(b.qty),'source_tradeIDs':list(b.ids),'invalid_source_ID_count':b.invalid_ids,'internal_duplicate_source_IDs':b.duplicate_ids,'in_strict_common_prefix':common,'local_whole_batch_eligible':e['local_full'],'batch_label_conflict':e['conflict'],'references':reference_records,'price_basis':'equal price guaranteed only by frozen same-price branch; no raw price independently read' if kind=='equal' else 'NONTRANSFERABLE: own price differs under crossing model'}
      audit.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n')
      # Fixed first witness for each reason/path, never chosen by label value.
      for rr in reference_records:
       wk=(k,kind,rr['technical'],rr['transfer'])
       if wk not in reasons_witness:reasons_witness[wk]={'day':day,'model':k[0],'delay_ms':k[1],'policy':k[2],'ledger_row':n,'t':t,'virtual_order_id':b.order_id,'kind':kind,'reference':rr}
     else:other[k][side+'|'+kind]+=1
    if n%2048==0:guard.check()
 if h.h.hexdigest()!=src['sealed_sha256'] or h.n!=src['sealed_compressed_bytes'] or n!=src['sealed_data_rows_excluding_CSV_header_if_any']:raise ValueError('Ledger SHA/bytes/row drift')
 pathout=[];cellout=[]
 for k in paths:
  original=next(x for x in inv['path_universe'] if (x['day'],x['model'],x['delay_ms'],x['policy'])==(day,*k))
  pathout.append({'day':day,'model':k[0],'delay_ms':k[1],'policy':k[2],'original_frozen':original['frozen'],'original_execution_cash_status':original['execution_cash_status'],'common_prefix_cutoff_exclusive':cutoffs[(day,k[0],k[1])],'saved_rows':rows[k],'all_fill_records':fill_count[k],'other_fill_kind_records':dict(other[k]),'all_saved_maker_buy_coverage':paths[k].finish(False),'strict_common_prefix_coverage':prefix_metrics[k].finish(False),'no_path_specific_primary_statistic':True})
 for k,metric in cells.items():
  result=metric.finish(True);cut=cutoffs[(day,*k)]
  prefix_elig=result['primary']['descriptive_eligibility']
  result['primary']['scope']='STRICT_COMMON_PREFIX_NOT_FULL_WINDOW' if cut is not None else 'ORIGINAL_FULL_WINDOW'
  if cut is not None:
   result['primary']['prefix_descriptive_eligibility']=prefix_elig;result['primary']['full_window_eligibility']='UNKNOWN_FROZEN';result['primary']['full_window_interpretation']=None
  else:result['primary']['full_window_eligibility']=prefix_elig;result['primary']['full_window_interpretation']=result['primary']['interpretation']
  cellout.append({'day':day,'model':k[0],'delay_ms':k[1],'common_prefix_cutoff_exclusive':cut,'support_definition':'F1/H1 equal source tradeID UNION; combined fill rows/quantities remain parallel records, never independent trades','metrics':result})
 return pathout,cellout,list(reasons_witness.values()),{'day':day,'kind':src['kind'],'path':src['path'],'sha256':h.h.hexdigest(),'bytes':h.n,'data_rows':n,'gzip_EOF_CRC':True}

def formal():
 seal=json.loads((OUT/'preparation-seal.json').read_text());release=json.loads((ROOT/'formal-release.json').read_text())
 if release.get('status')!='RELEASED_ONE_LABEL_LINKAGE' or release.get('preparation_seal_sha256')!=sha(OUT/'preparation-seal.json'):raise PermissionError('Root linkage release missing/mismatch')
 if source_hashes()!=seal['source_hashes'] or sha(OUT/'synthetic-receipt.json')!=seal['synthetic_receipt_sha256']:raise ValueError('Frozen helper/synthetic drift')
 inv,proto,small=context()
 if small!=seal['small_input_hashes'] or sys.executable!=seal['runtime_executable'] or sys.version!=seal['runtime_version']:raise ValueError('Preparation binding drift')
 cutoffs={}
 for day in proto['days']:
  src=next(x for x in inv['sources'] if x['day']==day and x['kind']=='inventory_exit_ledger');summary=json.loads(Path(src['summary_path']).read_text())
  for m in proto['models']:
   for delay in proto['delays_ms']:
    times=[]
    for p in proto['policies']:
     r=next(x for x in summary['results'] if (x['model'],x['delay_ms'],x['policy'])==(m,delay,p))
     if r.get('frozen'):
      if not r['unknown']:raise ValueError('Frozen summary missing original first unknown')
      times.append(integer(r['unknown'][0][0]))
    cutoffs[(day,m,delay)]=min(times) if times else None
 allpaths=[];allcells=[];witnesses=[];reads=[]
 with gzip.open(OUT/'linkage-audit.jsonl.gz','wt') as audit:
  for day in proto['days']:
   csrc=next(x for x in inv['sources'] if x['day']==day and x['kind']=='coverage');lsrc=next(x for x in inv['sources'] if x['day']==day and x['kind']=='inventory_exit_ledger')
   index,read=read_coverage(csrc);reads.append(read)
   paths,cells,wit,read=read_day_ledger(lsrc,index,inv,cutoffs,audit);allpaths.extend(paths);allcells.extend(cells);witnesses.extend(wit);reads.append(read);del index;guard.check()
 if len(allpaths)!=16 or len(allcells)!=8:raise ValueError('Universe path/cell denominator')
 save('paths-16.json',{'paths':allpaths,'path_specific_primary_statistics_not_computed':True})
 save('cells-8.json',{'cells':allcells,'no_CI_bootstrap_FH_second_primary':True})
 save('fixed-first-witnesses.json',{'definition':'first original ledger occurrence for each path/kind/technical/transfer reason, not selected by label result','witnesses':witnesses})
 save('result.json',{'status':'COMPLETED_SAVED_LABEL_LINKAGE_NOT_STRATEGY_REPLAY','utc':utc(),'input_read_receipts':reads,'all_paths':16,'all_cells':8,'cross_label_transfer_count':0,'new_labels_markout_or_price_reads':0,'interpretation_limit':'same-price support prints, not own fill allocation, real queue, causal alpha or net-profit proof','actual_model_effort_speed':'UNKNOWN'})
 return {'status':'COMPLETED_SAVED_LABEL_LINKAGE_NOT_STRATEGY_REPLAY','paths':16,'cells':8}

def main():
 global guard,PHASE
 PHASE=sys.argv[1] if len(sys.argv)>1 else None
 if PHASE not in ('prepare','formal'):raise ValueError('Use prepare or formal')
 if PHASE=='formal':save('formal-started.json',{'utc':utc(),'pid':os.getpid(),'runtime_executable':sys.executable,'runtime_version':sys.version,'source_hashes':source_hashes(),'formal_attempt':1})
 status='FAILED_STOP';code=1;err=None
 try:
  guard=Guard(PHASE);ans=prepare() if PHASE=='prepare' else formal();status=ans['status'];code=0;print(json.dumps(ans))
 except BaseException as e:err={'type':type(e).__name__,'message':str(e)}
 finally:
  save(PHASE+'-completion-'+str(time.time_ns())+'.json',{'utc':utc(),'pid':os.getpid(),'status':status,'exit_code':code,'error':err,'runtime_executable':sys.executable,'runtime_version':sys.version,'source_hashes':source_hashes()})
  if guard is not None:guard.finish(status)
 sys.exit(code)
if __name__=='__main__':main()
