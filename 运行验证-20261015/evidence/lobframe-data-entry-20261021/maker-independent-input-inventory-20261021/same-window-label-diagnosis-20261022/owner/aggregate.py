"""Only aggregate immutable coverage labels; never import prior engine/analysis or market readers."""
import os,sys,time,signal,resource,json,gzip,io,math,random,hashlib,calendar
from collections import Counter,defaultdict
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;UNIT=OUT.parent.parent;PRIOR=UNIT/'execution-20261022'/'owner'
BOOT=time.monotonic();DAYS=('2026-05-01','2026-06-01');CELL=('z_buy','z_sell','hash_buy','hash_sell');T=10_000_000
DEADLINE=calendar.timegm((2026,10,22,12,16,20));MANIFEST_SHA='a3121ebb335fd9950e86c16f739fb957d67aa583d65fe3066f968243f208e903'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
 with (OUT/n).open('x') as f:json.dump(x,f,ensure_ascii=True,indent=2,allow_nan=False);f.write('\n')
class Budget:
 def __init__(self,phase):
  self.phase=phase;self.prior=sum(json.loads(p.read_text())['CPU_seconds'] for p in OUT.glob('resource-*.json'))
  left=20-self.prior
  if left<=0:raise TimeoutError('Owner20CPU exhausted')
  resource.setrlimit(resource.RLIMIT_CPU,(max(1,int(left)),max(2,int(left)+1)))
  signal.signal(signal.SIGXCPU,self.exceeded);signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,.5,.5);self.guard()
 def exceeded(self,*args):raise TimeoutError('RLIMIT_CPU')
 def guard(self,*args):
  if time.time()>=DEADLINE or self.prior+time.process_time()>=20:raise TimeoutError('deadline/Owner20CPU')
  if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>134217728:raise MemoryError('128MiB')
  if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2097152:raise OSError('2MiB')
 def finish(self,status):
  signal.setitimer(signal.ITIMER_REAL,0)
  save('resource-'+self.phase+'-'+str(time.time_ns())+'.json',{'utc':utc(),'status':status,'phase':self.phase,'CPU_seconds':time.process_time(),'prior_Owner_CPU_seconds':self.prior,'review_Root_reserve_seconds':10,'cumulative_debit_including_reserve':self.prior+time.process_time()+10,'wall_seconds':time.monotonic()-BOOT,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'output_bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'pid':os.getpid(),'threads':1,'network':0,'actual_model_effort_speed':'UNKNOWN'})
class Aggregate:
 def __init__(self,first,last,nblocks):
  self.first=first;self.last=last;self.nblocks=nblocks;self.den=0;self.ref=0;self.status=Counter();self.reasons=Counter();self.grid_reasons={};self.cells=defaultdict(list);self.ids=[set() for _ in CELL];self.orders=[0]*4
 def add(self,r):
  sec=r['grid_second']
  if not self.first<=sec<=self.last:return
  self.den+=1;self.ref+=int(r['reference_qualified']);self.status[str(r['status'])]+=1;self.reasons[str(r.get('grid_reason'))]+=1
  reason=r.get('grid_reason')
  if sec in self.grid_reasons and self.grid_reasons[sec]!=reason:raise ValueError('Stored reason inconsistent within grid')
  self.grid_reasons[sec]=reason
  if r['status']!='selected_first':return
  if not r['reference_qualified'] or r['label'] is None:raise ValueError('selected_first without qualified stored label')
  loss=r['label']['loss_bp']
  if not isinstance(loss,(int,float)) or not math.isfinite(loss):raise ValueError('Invalid stored loss')
  side=r['passive_side'];ident=r['buy_order_id'] if side=='buy' else r['sell_order_id']
  for p,hint in enumerate((r['z_side'],r['hash_side'])):
   if hint==side:
    c=2*p+(0 if side=='buy' else 1);self.cells[(sec,c)].append(float(loss));self.ids[c].add(ident);self.orders[c]+=1
 def result(self):
  per=[[] for _ in CELL];blocks=[[[0.,0] for _ in CELL] for _ in range(self.nblocks)]
  for (sec,c),losses in self.cells.items():
   mean=math.fsum(losses)/len(losses);per[c].append(mean);b=sec//1800
   blocks[b][c][0]+=mean;blocks[b][c][1]+=1
  counts=[len(v) for v in per];sums=[math.fsum(v) for v in per];means=[sums[c]/counts[c] if counts[c] else None for c in range(4)]
  d=None if any(x is None for x in means) else .5*((means[0]-means[2])+(means[1]-means[3]))
  return {'grid_first':self.first,'grid_last':self.last,'fixed_label_denominator':self.den,'reference_qualified_numerator':self.ref,'reference_UNKNOWN_count':self.den-self.ref,'label_coverage_fraction':self.ref/self.den if self.den else None,'coverage_80pct_pass':bool(self.den and self.ref*5>=self.den*4),'status_row_counts':dict(self.status),'stored_grid_reason_row_counts':dict(self.reasons),'stored_reason_observed_unique_grid_counts':dict(Counter(str(v) for v in self.grid_reasons.values())),'unique_grids_represented_in_coverage_rows':len(self.grid_reasons),'full_grid_total':self.last-self.first+1,'unrepresented_grid_reason':'not inferable from coverage rows; no grid_states run','cell_order':list(CELL),'cell_distinct_passive_ID_counts':[len(x) for x in self.ids],'cell_selected_order_counts':self.orders,'cell_valid_grid_counts':counts,'cell_sum_of_grid_means':sums,'L_policy_direction':means,'D_day_bp':d,'minimum100_IDs_eachcell_pass':all(len(x)>=100 for x in self.ids),'blocks30min':blocks,'original_selected_first_not_recomputed':True,'missing_reference_detailed_reason':'coverage stores generic reference_UNKNOWN, no new future reason inferred'}
def type7(vals,q):
 v=sorted(vals);x=(len(v)-1)*q;i=int(x);f=x-i;return v[i]+(v[min(i+1,len(v)-1)]-v[i])*f

def bootstrap(days,R=1999,seed=20261021):
 rng=random.Random(seed);values=[[],[]];combo=[];invalid=[0,0];drawhash=hashlib.sha256()
 for rep in range(R):
  dd=[]
  for j,day in enumerate(days):
   indices=[rng.randrange(19) for _ in range(19)];drawhash.update(bytes(indices));s=[0.]*4;n=[0]*4
   for b in indices:
    for c in range(4):s[c]+=day['blocks30min'][b][c][0];n[c]+=day['blocks30min'][b][c][1]
   if any(x==0 for x in n):dd.append(None);invalid[j]+=1
   else:
    m=[s[c]/n[c] for c in range(4)];v=.5*((m[0]-m[2])+(m[1]-m[3]));values[j].append(v);dd.append(v)
  if all(x is not None for x in dd):combo.append(.5*(dd[0]+dd[1]))
 def summary(v):return {'valid_replicates':len(v),'invalid_replicates':R-len(v),'minimum1900_pass':len(v)>=1900,'CI_type7_2_5_97_5':[type7(v,.025),type7(v,.975)] if len(v)>=1900 else None}
 return {'method':'19 UTC-aligned truncated30minute units/day, retain empty/edge blocks; joint4cell sum/count; perrep May19 thenJune19','seed':seed,'replicates':R,'daily':[summary(v) for v in values],'equal_two_day_auxiliary':summary(combo),'draw_indices_sha256':drawhash.hexdigest(),'descriptive_not_independent_OOS':True}
class HashingReader:
 def __init__(self,f):self.f=f;self.h=hashlib.sha256();self.n=0
 def read(self,n=-1):
  b=self.f.read(n);self.h.update(b);self.n+=len(b);return b

def identities():
 manifest=PRIOR/'final-manifest.json'
 if sha(manifest)!=MANIFEST_SHA:raise ValueError('Old final manifest identity')
 files={r['path']:r for r in json.loads(manifest.read_text())['files']};small={};cov=[]
 for name in ('analysis.py','parameters.json',DAYS[0]+'-summary.json',DAYS[1]+'-summary.json'):
  if sha(PRIOR/name)!=files[name]['sha256']:raise ValueError('Old small input hash drift')
  small[name]=files[name]['sha256']
 for day in DAYS:
  name=day+'-coverage.jsonl.gz';f=PRIOR/name;entry=files[name];st=f.stat()
  if st.st_size!=entry['bytes']:raise ValueError('Coverage size drift')
  cov.append({'day':day,'path':str(f),'bytes':entry['bytes'],'sha256':entry['sha256'],'stat_mtime_ns':st.st_mtime_ns})
 return {'manifest_sha256':MANIFEST_SHA,'small_sha256':small,'coverage':cov}

def validate_row(r,start):
 sec=r['grid_second'];capture=r['capture_ticks']
 if not isinstance(sec,int) or not 5<=sec<=86394 or (capture-start-1)//T!=sec:raise ValueError('Stored capture/grid incompatible')
 if r['passive_side'] not in ('buy','sell') or r['z_side'] not in ('buy','sell',None) or r['hash_side'] not in ('buy','sell',None):raise ValueError('Stored side enum')
 if not isinstance(r['reference_qualified'],bool) or r['reference_qualified']!=(r['label'] is not None):raise ValueError('Saved qualification/label mismatch')

def parity(all_day,old):
 for a,b in ((all_day['fixed_label_denominator'],old['fixed_denominator']),(all_day['reference_qualified_numerator'],old['label_coverage_numerator']),(all_day['cell_distinct_passive_ID_counts'],old['independent_ID_counts']),(all_day['cell_valid_grid_counts'],old['valid_grid_counts'])):
  if a!=b:raise ValueError('All-day exact reference parity')
 for x,y in zip(all_day['cell_sum_of_grid_means'],old['sum_of_grid_order_means']):
  if abs(x-y)>1e-10:raise ValueError('All-day sum parity')
 if abs(all_day['D_day_bp']-old['D_day'])>1e-12:raise ValueError('All-day D reference parity')
 return {'passed':True,'old_D_quoted_not_new_effect':old['D_day'],'D_absolute_difference':abs(all_day['D_day_bp']-old['D_day']),'grid_sum_absolute_tolerance':1e-10,'D_absolute_tolerance':1e-12,'only_validation_not_independent_effect':True}

def prepare(budget):
 import synthetic
 checks=synthetic.run();save('synthetic-receipt.json',{'utc':utc(),'checks':checks,'count':len(checks),'all_pass':True,'uses_real_coverage':False,'script_hashes':{n:sha(OUT/n) for n in ('aggregate.py','synthetic.py','method-spec.json')}})
 x=identities();save('preparation-seal.json',{'utc':utc(),'input_identities':x,'source_sha256':{n:sha(OUT/n) for n in ('aggregate.py','synthetic.py','method-spec.json')},'runtime':sys.executable,'version':sys.version,'authorization_sha256':sha(OUT.parent/'root'/'authorization.json'),'synthetic_receipt_sha256':sha(OUT/'synthetic-receipt.json'),'no_coverage_decoded':True})
 return {'status':'PREPARED_NO_SAME_WINDOW_RESULT','synthetic_checks':len(checks)}
def formal(budget):
 seal=json.loads((OUT/'preparation-seal.json').read_text());release=json.loads((OUT.parent/'root'/'formal-release.json').read_text())
 if release.get('status')!='RELEASED_ONE_CACHED_LABEL_AGGREGATION' or release.get('preparation_seal_sha256')!=sha(OUT/'preparation-seal.json'):raise PermissionError('Root release mismatch')
 if sys.executable!=seal['runtime'] or sys.version!=seal['version']:raise ValueError('Runtime drift')
 if sha(OUT.parent/'root'/'authorization.json')!=seal['authorization_sha256'] or identities()!=seal['input_identities']:raise ValueError('Frozen identity drift')
 for n,h in seal['source_sha256'].items():
  if sha(OUT/n)!=h:raise ValueError('Source drift')
 days=[];validation=[];reads=[]
 for inp in seal['input_identities']['coverage']:
  day=inp['day'];start=calendar.timegm(datetime.strptime(day,'%Y-%m-%d').timetuple())*T
  win=Aggregate(5,32449,19);all_day=Aggregate(5,86394,48);rows=0;last=-1
  with open(inp['path'],'rb') as raw:
   hr=HashingReader(raw)
   with gzip.GzipFile(fileobj=hr,mode='rb') as gz:
    with io.TextIOWrapper(gz,encoding='utf-8') as text:
     for line in text:
      r=json.loads(line);validate_row(r,start)
      if r['capture_ticks']<last:raise ValueError('Coverage chronology drift')
      last=r['capture_ticks'];win.add(r);all_day.add(r);rows+=1
      if rows%1000==0:budget.guard()
   if hr.h.hexdigest()!=inp['sha256'] or hr.n!=inp['bytes']:raise ValueError('Coverage compressed SHA/size mismatch')
  w=win.result();w['day']=day;days.append(w)
  old=json.loads((PRIOR/(day+'-summary.json')).read_text());validation.append({'day':day,**parity(all_day.result(),old)})
  reads.append({'day':day,'rows_read':rows,'compressed_sha256':hr.h.hexdigest(),'compressed_bytes':hr.n,'gzip_EOF_CRC':True,'single_numeric_scan':True})
  del win,all_day
  budget.guard()
 uncertainty=bootstrap(days);budget.guard()
 for i,d in enumerate(days):d['descriptive_uncertainty']=uncertainty['daily'][i]
 equal=.5*(days[0]['D_day_bp']+days[1]['D_day_bp']) if all(d['D_day_bp'] is not None for d in days) else None
 result={'status':'COMPLETE_CACHED_LABEL_EXACT_WINDOW_DIAGNOSTIC','window_grid':[5,32449],'days':days,'uncertainty':uncertainty,'equal_day_D_auxiliary_bp':equal,'all_day_implementation_validation_only':validation,'input_read_receipts':reads,'no_new_labels_or_firstID_or_grid_states_or_strategy':True,'no_economic_or_alpha_claim':True,'actual_model_effort_speed':'UNKNOWN'}
 save('result.json',result)
 return {'status':result['status'],'daily':[{'day':d['day'],'D_day_bp':d['D_day_bp'],'denominator':d['fixed_label_denominator'],'qualified':d['reference_qualified_numerator'],'ID_counts':d['cell_distinct_passive_ID_counts'],'grid_counts':d['cell_valid_grid_counts'],'uncertainty':d['descriptive_uncertainty']} for d in days],'equal_day_D_auxiliary_bp':equal}

def main():
 phase=sys.argv[1] if len(sys.argv)>1 else ''
 if phase not in ('prepare','formal'):raise ValueError('Explicit phase')
 if (OUT/'first-stop.json').exists():raise RuntimeError('Terminal STOP')
 if phase=='formal':save('formal-started.json',{'utc':utc(),'pid':os.getpid(),'executable':sys.executable,'version':sys.version,'argv':sys.argv})
 b=None;status='FAILED_STOP'
 try:
  b=Budget(phase);r=prepare(b) if phase=='prepare' else formal(b);status=r['status'];print(json.dumps(r),flush=True);save(phase+'-completion.json',{'utc':utc(),'pid':os.getpid(),'exit_code':0,'status':status})
 except BaseException as e:
  if phase=='formal' and not (OUT/'first-stop.json').exists():save('first-stop.json',{'utc':utc(),'type':type(e).__name__,'message':str(e),'no_retry':True})
  elif phase=='prepare':save('prepare-failure-'+str(time.time_ns())+'.json',{'utc':utc(),'type':type(e).__name__,'message':str(e)})
  raise
 finally:
  if b:b.finish(status)
if __name__=='__main__':main()
