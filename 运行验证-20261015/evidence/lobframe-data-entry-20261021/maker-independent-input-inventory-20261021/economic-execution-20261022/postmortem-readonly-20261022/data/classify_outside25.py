"""Read-only ledger event classification; never imports Owner code or creates orders."""
import csv,gzip,json,time,resource,signal,hashlib,os,sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
from collections import Counter
OUT=Path(__file__).resolve().parent
OWNER=OUT.parents[1]/'owner'
CPU=time.process_time(); WALL=time.monotonic()
T=10000000
progress={'ledger_rows':{},'events_found':{},'events_classified':0}
def utc(): return datetime.now(timezone.utc).isoformat()
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (OUT/n).open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def guard(*a):
 if time.process_time()-CPU>=44: raise TimeoutError('CPU guard44s (hard45)')
 if time.monotonic()-WALL>=180: raise TimeoutError('wall180s')
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>134217728: raise MemoryError('RSS128MiB')
 if sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())>4194304: raise OSError('output4MiB')
def dt(t):
 s,f=divmod(t,T);return datetime.fromtimestamp(s,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')+'.'+str(f).zfill(7)+'Z'
def main():
 resource.setrlimit(resource.RLIMIT_CPU,(45,46));signal.signal(signal.SIGXCPU,guard)
 manifest=json.loads((OWNER/'final-manifest.json').read_text()); seal=json.loads((OWNER/'preparation-seal.json').read_text())
 mi={x['path']:x for x in manifest['files']}
 save('started.json',{'utc':utc(),'pid':os.getpid(),'script_sha256':digest(Path(__file__)),'owner_manifest_sha256':digest(OWNER/'final-manifest.json'),'preparation_seal_sha256':digest(OWNER/'preparation-seal.json'),'constraints':{'CPU_seconds':45,'RSS_bytes':134217728,'output_bytes':4194304,'threads':1,'network':0},'method':'All UNKNOWN_queue_outside25 ledger events, strict capture<t latest group; same original source<t, age<=1s, source regression and numeric100field same-capture conflict rules; no older fallback. Categories spread_improvement/deeper_same_side/other_unmatched. Fixed first means original ledger physical first per day/category. No replay or financial calculation.'})
 counts=Counter(); witnesses={}; identities=[]; all_event_count=0
 with (OUT/'classified-events.jsonl').open('x') as ef:
  for day in ('2026-05-01','2026-06-01'):
   lp=OWNER/(day+'-ledger.csv.gz'); rec=mi[lp.name]
   if lp.stat().st_size!=rec['bytes']:raise ValueError('ledger size drift')
   events=[]; n=0
   with gzip.open(lp,'rt',newline='') as f:
    rd=csv.DictReader(f)
    for n,r in enumerate(rd,1):
     if r['event']=='UNKNOWN_queue_outside25':
      events.append({'date':day,'ledger_row':n,'capture_ticks':int(r['t']),'side':r['side'],'own_limit':r['limit'],'model':r['model'],'delay_ms':r['delay_ms'],'policy':r['policy'],'order_id':r['order_id']})
     if n%4096==0:guard()
   progress['ledger_rows'][day]=n;progress['events_found'][day]=len(events);all_event_count+=len(events)
   # Stable physical ledger order is retained for witnesses; sorting only drives an as-of join.
   events.sort(key=lambda e:(e['capture_ticks'],e['ledger_row']))
   q=next(x for x in seal['inputs']['BBO'] if x['date']==day);bp=Path(q['path']);st=bp.stat()
   if st.st_size!=q['stat_size'] or st.st_mtime_ns!=q['stat_mtime_ns']:raise ValueError('BBO frozen stat drift')
   identities.append({'date':day,'ledger':str(lp),'ledger_manifest_sha256':rec['sha256'],'ledger_full_gzip_EOF_CRC_read':True,'book':q,'book_full_hash_CRC_not_rerun':True})
   ei=0;previous=None;g=None;maxsrc=-1;prev_cap=-1
   def classify(e,book):
    nonlocal counts
    category='other_unmatched';reason='no_prior_book'; witness=None
    if book is not None:
     cap,src,row,vals,bad=book;t=e['capture_ticks']
     witness={'book_row':row,'capture_ticks':cap,'capture_utc':dt(cap),'source_us':src,'ask':vals[0],'bid':vals[2],'ask25':vals[96],'bid25':vals[98],'invalid_group':bad,'age_ticks':t-cap}
     if bad:reason='conflict_or_source_regression'
     elif not cap<t:reason='capture_not_strict_prior'
     elif src*10>=t:reason='source_not_prior'
     elif t-cap>T:reason='older_than_fixed_1s'
     else:
      L=Decimal(e['own_limit']);ask=Decimal(vals[0]);bid=Decimal(vals[2]);ask25=Decimal(vals[96]);bid25=Decimal(vals[98])
      if bid<L<ask:category='spread_improvement';reason='inside_spread_excluded_by_model_same_side_range'
      elif (e['side']=='buy' and L<bid25) or (e['side']=='sell' and L>ask25):category='deeper_same_side';reason='beyond_visible_same_side_depth'
      else:reason='other_price_or_event_inconsistency'
    x={**e,'event_utc':dt(e['capture_ticks']),'category':category,'reason':reason,'reference':witness}
    counts[(day,e['model'],e['delay_ms'],e['policy'],category)]+=1
    key=(day,category)
    if key not in witnesses or e['ledger_row']<witnesses[key]['ledger_row']:witnesses[key]=x
    ef.write(json.dumps(x,ensure_ascii=False)+'\n');progress['events_classified']+=1
   def flush(group):
    nonlocal previous,ei
    if group is None:return
    # At exact equality use the previous capture group; never the arriving group.
    while ei<len(events) and events[ei]['capture_ticks']<=group[0]:
     classify(events[ei],previous);ei+=1
    previous=group
   fields=[f'{side}[{i}].{v}' for i in range(25) for side in ('asks','bids') for v in ('price','amount')]
   start=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())*T
   with gzip.open(bp,'rt',newline='') as f:
    rd=csv.DictReader(f)
    if set(rd.fieldnames)!=set(['exchange','symbol','timestamp','local_timestamp']+fields):raise ValueError('book schema')
    for rn,r in enumerate(rd,1):
     cap=int(r['local_timestamp'])*10
     if cap>start+32452*T:break
     if cap<prev_cap or r['exchange']!='bitstamp' or r['symbol']!='BTCUSD':raise ValueError('book identity/order')
     src=int(r['timestamp']);vals=tuple(r[k] for k in fields);bad=src<maxsrc;maxsrc=max(src,maxsrc)
     if g is not None and cap==g[0]:
      same=vals==g[3] or tuple(map(Decimal,vals))==tuple(map(Decimal,g[3]))
      g=(cap,src,rn,vals,g[4] or bad or not same)
     else:flush(g);g=(cap,src,rn,vals,bad)
     prev_cap=cap
     if rn%2048==0:guard()
   flush(g)
   while ei<len(events):classify(events[ei],previous);ei+=1
   guard()
 rows=[dict(zip(['date','model','delay_ms','policy','category'],k),count=v) for k,v in sorted(counts.items())]
 save('classification-summary.json',{'status':'COMPLETE','definitions':{'spread_improvement':'bid<own_limit<ask (either side)','deeper_same_side':'buy own_limit<bid25; sell own_limit>ask25','other_unmatched':'invalid/missing strict reference or other event-price mismatch'},'denominator':all_event_count,'coverage':progress,'counts':rows,'fixed_first_witnesses':list(witnesses.values()),'input_identities':identities,'risk_unknown':'No risk values rescanned/recomputed. Fixed1s freshness is model constraint, not proof of physical disconnect; source numeric granularity is not clock accuracy.'})
if __name__=='__main__':
 status='FAILED_STOP';error=None;code=1
 try:main();status='COMPLETE';code=0
 except BaseException as e:error={'type':type(e).__name__,'message':str(e)}
 finally:
  save('completion.json',{'utc':utc(),'pid':os.getpid(),'status':status,'exit_code':code,'error':error,'coverage':progress,'CPU_seconds':time.process_time()-CPU,'wall_seconds':time.monotonic()-WALL,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'output_bytes_before_receipt':sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()),'script_sha256':digest(Path(__file__)),'network':0,'threads':1,'no_model_import_execution':True,'no_financial_calculation':True})
 sys.exit(code)
