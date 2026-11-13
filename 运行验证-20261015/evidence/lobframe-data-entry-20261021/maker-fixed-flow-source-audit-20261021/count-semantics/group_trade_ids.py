"""One local CSV-only identity grouping, no source market payload access."""
import time,os
START=time.monotonic();CPU=time.process_time()
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import csv,json,hashlib,resource,signal
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
SOURCE=R.parent.parent/'maker-trade-previsibility-20261021/identity-time/trade-coverage.csv'
EXPECTED='2eb45b82cf7d4aa11c31948f735a02ab58f34d760886d049a9f0642836cf0265'
def now():return datetime.now(timezone.utc).isoformat()
def write(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def main():
 if (R/'started.json').exists():raise RuntimeError('Single CSV grouping already started')
 write('started.json',{'utc':now(),'pid':os.getpid(),'input':str(SOURCE),'expected_sha256':EXPECTED,'source_market_body_opened':False,'analysis_attempts':1})
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('60second limit')));signal.alarm(60)
 receipt={'utc_start':now(),'networks':0,'financial_computations':False,'source_market_body_opened':False,'actual_model':'UNKNOWN','actual_effort':'UNKNOWN'}
 try:
  raw=SOURCE.read_bytes();actual=hashlib.sha256(raw).hexdigest();receipt['csv_sha256']=actual
  if actual!=EXPECTED:raise RuntimeError('CSV identity mismatch')
  rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
  if len(rows)!=50:raise RuntimeError('Fixed denominator not50')
  groups=defaultdict(list);unknown=[];all_witness=[]
  for row in rows:
   typ=row['raw_type']
   if typ not in ('0','1'):unknown.append(row['line']);continue
   active=row['buy_order_id'] if typ=='0' else row['sell_order_id'];passive=row['sell_order_id'] if typ=='0' else row['buy_order_id']
   if not active:unknown.append(row['line']);continue
   w={'source_csv_line':len(all_witness)+2,'raw_response_trade_line':row['line'],'trade_id':row['trade_id'],'raw_type':typ,
      'aggressor_side_by_supplier_mapping':'buy' if typ=='0' else 'sell','active_order_id':active,'passive_order_id':passive,
      'buy_order_id':row['buy_order_id'],'sell_order_id':row['sell_order_id'],'local_exact':row['local_exact'],'local_ticks':row['local_ticks'],'source_microtimestamp_exact':row['source_microtimestamp_exact']}
   groups[(typ,active)].append(w);all_witness.append(w)
  grouped=[];counts={}
  for typ,side in (('0','buy'),('1','sell')):
   subset=[(key,vals) for key,vals in groups.items() if key[0]==typ]
   total=sum(len(vals) for _,vals in subset);duplicate=[(key,vals) for key,vals in subset if len(vals)>1]
   counts[side]={'raw_type':int(typ),'trade_reports':total,'distinct_aggressor_order_ids':len(subset),'multi_trade_aggressor_id_groups':len(duplicate),
                'trade_reports_in_multi_trade_id_groups':sum(len(vals) for _,vals in duplicate),'duplicate_trade_count_beyond_one_per_id':sum(len(vals)-1 for _,vals in duplicate),
                'per_active_id_trade_count_distribution':dict(Counter(str(len(vals)) for _,vals in subset))}
  for (typ,active),vals in groups.items():
   grouped.append({'raw_type':int(typ),'aggressor_side_by_supplier_mapping':'buy' if typ=='0' else 'sell','active_order_id':active,'trade_count':len(vals),'distinct_passive_order_ids':len({x['passive_order_id'] for x in vals}),'witnesses':vals})
  summary={'status':'CSV_IDENTITY_GROUPING_COMPLETE','source_csv':str(SOURCE),'source_csv_sha256':actual,'fixed_denominator':50,'recognized_rows':len(all_witness),'unknown_rows':unknown,
   'counts_by_aggressor_side':counts,'total_distinct_direction_and_active_id_groups':len(groups),
   'meaning':'Report count differs from distinct active orderID count when one observed ID links multiple trade reports; no reconstruction of parent orders, order quantities, institution identity, execution economics or strategy'}
  write('counts.json',summary);write('all-id-groups.json',{'all50_denominator':50,'groups':grouped});write('duplicate-id-witnesses.json',{'all50_denominator':50,'mechanical_selection':'all groups with trade_count>1; no outcome selection','groups':[x for x in grouped if x['trade_count']>1]})
  with (R/'all50-identity-witnesses.csv').open('x',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=list(all_witness[0]));writer.writeheader();writer.writerows(all_witness)
  receipt['status']=summary['status']
 except BaseException as exc:receipt.update(status='FAIL_NO_RERUN',error_type=type(exc).__name__,error_message=str(exc))
 finally:
  signal.alarm(0);receipt.update(utc_end=now(),wall_seconds=time.monotonic()-START,process_cpu_seconds=time.process_time()-CPU,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,threads_used=1,new_disk_bytes=sum(p.stat().st_size for p in R.iterdir() if p.is_file()),payments=0,downloads=0)
  if receipt['peak_rss_bytes']>256*1024*1024 or receipt['new_disk_bytes']>1024*1024:receipt['status']='FAIL_RESOURCE_CAP'
  write('check-receipt.json',receipt)
 print(json.dumps(receipt))
if __name__=='__main__':main()
