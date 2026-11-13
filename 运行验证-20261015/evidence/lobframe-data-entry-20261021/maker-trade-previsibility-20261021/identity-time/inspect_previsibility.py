"""Single cached-ID/time analysis; no prices/amounts, model or trading code."""
import os,time
START=time.monotonic();CPU=time.process_time()
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
import calendar,csv,gzip,hashlib,io,json,re,resource,signal
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
SOURCE=R.parent.parent/'maker-raw-one-minute-qc-20261021/raw-response.bin'
EXPECTED='6a345dff5cb142375e879fdee7fe2e71421d580209c8a13a0773d456fc0845d7'
CANDIDATE={'snapshot','order_created','order_changed'}

def now():return datetime.now(timezone.utc).isoformat()
def write(name,obj):
 with (R/name).open('x') as f:json.dump(obj,f,ensure_ascii=True,indent=2,allow_nan=False);f.write('\n')
def guard():
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>256*1024*1024:raise RuntimeError('256MiB memory cap')
 if sum(p.stat().st_size for p in R.rglob('*') if p.is_file())>16*1024*1024:raise RuntimeError('16MiB disk cap')
def ticks(s):
 m=re.fullmatch(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{7})Z',s)
 if not m:raise ValueError('Expected exact seven-digit UTC capture timestamp')
 return calendar.timegm(datetime.strptime(m[1],'%Y-%m-%dT%H:%M:%S').timetuple())*10_000_000+int(m[2])
def source_us(x):
 if not isinstance(x,(str,int)) or isinstance(x,bool):raise ValueError('Native microtimestamp type')
 s=str(x)
 if not s.isdigit():raise ValueError('Native microtimestamp not integer text')
 return int(s)
def enrich(ref,trade):
 if ref is None:return None
 return {**ref,'capture_relation_to_trade':'before' if ref['local_ticks']<trade['local_ticks'] else 'after' if ref['local_ticks']>trade['local_ticks'] else 'same',
  'source_relation_to_trade':'before' if ref['source_us']<trade['source_us'] else 'after' if ref['source_us']>trade['source_us'] else 'same',
  'collector_before_report_lead_100ns_ticks':trade['local_ticks']-ref['local_ticks'],
  'source_clock_lead_microseconds':trade['source_us']-ref['source_us']}
def coverage(identity,trade,allrefs):
 refs=sorted(allrefs.get(identity,[]),key=lambda x:(x['line'],x['field'])) if identity is not None else []
 before=[x for x in refs if x['local_ticks']<trade['local_ticks']]
 same=[x for x in refs if x['local_ticks']==trade['local_ticks']]
 after=[x for x in refs if x['local_ticks']>trade['local_ticks']]
 strict=[x for x in before if x['event'] in CANDIDATE and x['source_us']<trade['source_us']]
 same_source=[x for x in refs if x['source_us']==trade['source_us']]
 first=refs[0] if refs else None
 snaps=[x for x in refs if x['event']=='snapshot'];orders=[x for x in refs if x['event']!='snapshot']
 flags={'A_any_ID_strictly_before_collector_trade_report':bool(before),
  'B_candidate_state_strictly_before_on_both_clocks':bool(strict),
  'C_any_ref_same_source_microtimestamp':bool(same_source),
  'C_first_seen_is_changed_or_deleted':bool(first and first['event'] in ('order_changed','order_deleted')),
  'C_first_changed_deleted_same_source_timestamp':bool(first and first['event'] in ('order_changed','order_deleted') and first['source_us']==trade['source_us']),
  'D_only_after_collector_trade_report':bool(refs and len(after)==len(refs)),
  'E_no_ID_witness_in_window':not refs,'same_capture_timestamp_any':bool(same),
  'any_after_collector_trade_report':bool(after),
  'snapshot_strictly_before_collector_trade_report':any(x['local_ticks']<trade['local_ticks'] for x in snaps),
  'order_event_strictly_before_collector_trade_report':any(x['local_ticks']<trade['local_ticks'] for x in orders)}
 firstof=lambda xs:enrich(xs[0],trade) if xs else None
 return {'id':identity,'flags':flags,'reference_counts':{'all':len(refs),'capture_before':len(before),'capture_same':len(same),'capture_after':len(after)},
  'witnesses':{'first_any':enrich(first,trade),'A_first_before_capture':firstof(before),'B_first_candidate_both_before':firstof(strict),
   'first_same_capture':firstof(same),'first_after_capture':firstof(after),'first_snapshot':firstof(snaps),'first_order_event':firstof(orders),'first_same_source':firstof(same_source)}}

def main():
 if (R/'started.json').exists():raise RuntimeError('Already started: no rerun')
 spec=json.loads((R/'analysis-spec.json').read_text())
 actual_script=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 if actual_script!=spec['script_sha256']:raise RuntimeError('Script differs from frozen spec')
 write('started.json',{'utc':now(),'pid':os.getpid(),'script_sha256':actual_script,'source':str(SOURCE),'analysis_attempt':1})
 receipt={'utc_start':now(),'network_requests':0,'download_bytes':0,'actual_model':'UNKNOWN','actual_effort':'UNKNOWN','analysis_attempt':1}
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('30minute cap')));signal.setitimer(signal.ITIMER_REAL,1800)
 try:
  if SOURCE.is_symlink() or SOURCE.resolve()!=SOURCE:raise RuntimeError('Unexpected source path')
  raw=SOURCE.read_bytes();actual=hashlib.sha256(raw).hexdigest();receipt['source_sha256']=actual
  if actual!=EXPECTED:raise RuntimeError('Source hash mismatch')
  allrefs=defaultdict(list);trades=[];decoded=0;snapshots=0
  with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
   for line_no,line in enumerate(f,1):
    decoded+=len(line)
    if decoded>16*1024*1024:raise RuntimeError('Cached decoded size limit')
    if not line.strip():continue
    local,payload=line.decode('utf-8').rstrip('\r\n').split(' ',1);msg=json.loads(payload);dat=msg.get('data',{});ev=msg.get('event');channel=msg.get('channel')
    if channel not in ('live_orders_btcusd','live_trades_btcusd'):raise RuntimeError('Unexpected channel')
    if ev in ('snapshot','order_created','order_changed','order_deleted','trade'):
     ref={'line':line_no,'channel':channel,'event':ev,'local_exact':local,'local_ticks':ticks(local),'source_microtimestamp_exact':str(dat['microtimestamp']),'source_us':source_us(dat['microtimestamp'])}
     if ev=='snapshot' and channel=='live_orders_btcusd':
      snapshots+=1
      for side in ('bids','asks'):
       for idx,row in enumerate(dat[side]):
        if len(row)!=3 or not isinstance(row[2],str) or not row[2]:raise RuntimeError('Snapshot ID candidate shape drift')
        allrefs[row[2]].append({**ref,'field':f'data.{side}[{idx}][2]','snapshot_array_side':side})
     elif ev in ('order_created','order_changed','order_deleted') and channel=='live_orders_btcusd':
      if not isinstance(dat.get('id_str'),str) or dat['id_str']!=str(dat['id']):raise RuntimeError('Native order ID disagreement')
      allrefs[dat['id_str']].append({**ref,'field':'data.id_str (= str(data.id))'})
     elif ev=='trade' and channel=='live_trades_btcusd':
      value=dat.get('type');known=type(value) is int and value in (0,1)
      trades.append({**ref,'trade_id':str(dat['id']),'raw_type':value,'role_mapping_known':known,
        'aggressor_side_by_supplier_mapping':'buy' if value==0 else 'sell' if value==1 else 'UNKNOWN',
        'passive_side_by_supplier_mapping':'sell_ask' if value==0 else 'buy_bid' if value==1 else 'UNKNOWN',
        'buy_order_id':None if dat.get('buy_order_id') is None else str(dat['buy_order_id']),
        'sell_order_id':None if dat.get('sell_order_id') is None else str(dat['sell_order_id'])})
    if line_no%256==0:guard()
  if len(trades)!=50 or snapshots!=1:raise RuntimeError('Frozen sample denominator/shape differs')
  detailed=[];rows=[];counts={key:Counter() for key in ('buy','sell','passive')};types=Counter();special=[]
  for trade in trades:
   buy=coverage(trade['buy_order_id'],trade,allrefs);sell=coverage(trade['sell_order_id'],trade,allrefs)
   passive=sell if trade['raw_type']==0 and trade['role_mapping_known'] else buy if trade['raw_type']==1 and trade['role_mapping_known'] else None
   types[str(trade['raw_type'])]+=1
   entry={'trade':trade,'buy':buy,'sell':sell,'passive':passive};detailed.append(entry)
   row={k:trade[k] for k in ('line','trade_id','raw_type','role_mapping_known','aggressor_side_by_supplier_mapping','passive_side_by_supplier_mapping','local_exact','local_ticks','source_microtimestamp_exact','buy_order_id','sell_order_id')}
   for label,cov in (('buy',buy),('sell',sell),('passive',passive)):
    if cov is None:counts[label]['mapping_unknown']+=1;continue
    for flag,value in cov['flags'].items():row[label+'_'+flag]=value;counts[label][flag]+=int(value)
    for key,ref in cov['witnesses'].items():
     row[label+'_'+key+'_line']=None if ref is None else ref['line']
     row[label+'_'+key+'_event']=None if ref is None else ref['event']
     if key in ('A_first_before_capture','B_first_candidate_both_before'):
      row[label+'_'+key+'_capture_lead_100ns_ticks']=None if ref is None else ref['collector_before_report_lead_100ns_ticks']
    counts[label]['denominator']+=1
   if trade['line'] in (484,526):special.append(entry)
   rows.append(row);guard()
  if len(special)!=2:raise RuntimeError('Fixed historical match witness lines missing')
  fields=list(dict.fromkeys(k for row in rows for k in row))
  with (R/'trade-coverage.csv').open('x',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
  write('per-trade-field-witnesses.json',{'source_sha256':EXPECTED,'selection':'earliest source line within each declared category, not best lead/match/return','trades':detailed})
  write('historical-two-snapshot-matches.json',{'scope':'fixed trade lines484 and526; late snapshot cannot be prior input','trades':special})
  summary={'status':'ONE_CACHED_PREVISIBILITY_ANALYSIS_COMPLETE','source_sha256':EXPECTED,'trade_denominator':50,'raw_type_counts':dict(types),
   'counts':{k:dict(v) for k,v in counts.items()},'definitions':spec['definitions'],
   'categories_overlap':True,'no_orderbook_or_live_state_reconstruction':True,'snapshot_third_column_semantics':'candidate corroborated by prior ID equality, not independently authenticated official schema',
   'A_not_exchange_pretrade_actionability':True,'B_not_proof_cancellable_before_fill':True,'C_inducement_not_causally_proven':True,
   'same_capture_no_positive_advance_inferred_from_line_order':True,'side_roles_posthoc_labels_not_pretrade_features':True,'prices_amounts_returns_or_fees_output':False}
  write('counts.json',summary);receipt['status']=summary['status']
 except BaseException as exc:
  receipt.update(status='TERMINAL_LOCAL_ANALYSIS_FAILURE_NO_RERUN',error_type=type(exc).__name__,error_message=str(exc));write('terminal-stop.json',receipt)
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);guard();receipt.update(utc_end=now(),wall_seconds=time.monotonic()-START,process_cpu_seconds=time.process_time()-CPU,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,threads_used=1,new_disk_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file()),payments=0,installs=0)
  write('analysis-receipt.json',receipt)
 print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
