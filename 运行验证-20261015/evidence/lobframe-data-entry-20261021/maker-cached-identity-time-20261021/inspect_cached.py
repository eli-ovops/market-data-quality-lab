"""One local identity/time inspection. Never calculates market prices/amounts."""
import os,time
START=time.monotonic();CPU=time.process_time()
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
import calendar,gzip,hashlib,io,json,re,resource,signal
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
SOURCE=R.parent/'maker-raw-one-minute-qc-20261021/raw-response.bin'
EXPECTED='6a345dff5cb142375e879fdee7fe2e71421d580209c8a13a0773d456fc0845d7'
MEM=256*1024*1024
LIMIT=16*1024*1024

def now():return datetime.now(timezone.utc).isoformat()
def write(name,obj):
 with (R/name).open('x') as f:json.dump(obj,f,ensure_ascii=True,indent=2,allow_nan=False);f.write('\n')
def check():
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>MEM:raise RuntimeError('256MiB RSS limit')
 if sum(p.stat().st_size for p in R.rglob('*') if p.is_file())>LIMIT:raise RuntimeError('16MiB disk limit')
def local_ticks(text):
 m=re.fullmatch(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{1,7})Z',text)
 if not m:raise ValueError('Unexpected local timestamp syntax')
 sec=calendar.timegm(datetime.strptime(m[1],'%Y-%m-%dT%H:%M:%S').timetuple())
 return sec*10_000_000+int(m[2].ljust(7,'0')),len(m[2])
def event_ref(line,local,msg):
 dat=msg.get('data',{})
 return {'line':line,'channel':msg.get('channel'),'event':msg.get('event'),'local_timestamp_exact':local,
         'local_timestamp_100ns_epoch_ticks':str(local_ticks(local)[0]),
         'exchange_microtimestamp_exact':dat.get('microtimestamp'),
         'exchange_microtimestamp_field':'data.microtimestamp',
         'event_id_present':'event_id' in msg,'pre_event_id_present':'pre_event_id' in msg}
def relation(a,b):return 'less' if a<b else 'greater' if a>b else 'equal'

def main():
 if (R/'started.json').exists():raise RuntimeError('Local inspection already started')
 write('started.json',{'utc':now(),'pid':os.getpid(),'source':str(SOURCE),'expected_sha256':EXPECTED,'network_requests':0,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
 receipt={'utc_start':now(),'source':str(SOURCE),'expected_sha256':EXPECTED,'network_requests':0,'actual_model':'UNKNOWN','actual_effort':'UNKNOWN'}
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('30minute active limit')));signal.setitimer(signal.ITIMER_REAL,1800)
 try:
  if SOURCE.is_symlink() or SOURCE.resolve()!=SOURCE:raise RuntimeError('Source identity not project file')
  raw=SOURCE.read_bytes();receipt['actual_sha256']=hashlib.sha256(raw).hexdigest()
  if receipt['actual_sha256']!=EXPECTED:raise RuntimeError('Original source hash mismatch')
  ids=defaultdict(set);refs=defaultdict(dict);snapshot=None;previous=None;next_order=None
  fraction_digits=Counter();stats=Counter();decoded=0
  def register(kind,value,ref):
   if value is None:return
   text=str(value)
   if text=='':stats[kind+'_empty']+=1;return
   ids[kind].add(text)
   if text not in refs[kind]:refs[kind][text]=ref
  with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
   for line_no,line in enumerate(stream,1):
    decoded+=len(line)
    if decoded>16*1024*1024:raise RuntimeError('Unexpected cached uncompressed size')
    if not line.strip():continue
    prefix,payload=line.decode('utf-8').rstrip('\r\n').split(' ',1);msg=json.loads(payload);_,digits=local_ticks(prefix);fraction_digits[digits]+=1
    dat=msg.get('data',{});ev=msg.get('event');ch=msg.get('channel')
    if ev=='snapshot' and ch=='live_orders_btcusd':
     if snapshot is not None:raise RuntimeError('More than one snapshot; not expanding scope')
     snapshot={'reference':event_ref(line_no,prefix,msg),'generated':msg.get('generated'),'message_keys':sorted(msg),'data_keys':sorted(dat),'previous_order':previous,'sides':{}}
     for side in ('bids','asks'):
      arr=dat[side];values=[];non_string=0;empty=0;width=Counter()
      for i,row in enumerate(arr):
       width[len(row)]+=1
       if len(row)!=3:continue
       candidate=row[2]
       if not isinstance(candidate,str):non_string+=1;continue
       if not candidate:empty+=1;continue
       values.append(candidate)
      snapshot['sides'][side]={'entry_count':len(arr),'width_counts':dict(width),'third_column_nonstring':non_string,'third_column_empty':empty,
         'third_column_nonempty_count':len(values),'third_column_distinct_count':len(set(values)),'third_column_duplicate_excess':len(values)-len(set(values))}
      ids['snapshot_'+side].update(values)
      for i,row in enumerate(arr):
       if len(row)==3 and isinstance(row[2],str) and row[2]:refs['snapshot_'+side].setdefault(row[2],{'line':line_no,'field':f'data.{side}[{i}][2]','value':row[2]})
    elif ch=='live_orders_btcusd' and ev in ('order_created','order_changed','order_deleted'):
     ref=event_ref(line_no,prefix,msg);ref['id_str']=dat.get('id_str');ref['id_as_string']=None if dat.get('id') is None else str(dat['id'])
     stats['order_event_records']+=1
     if 'id_str' in dat and 'id' in dat:stats['order_id_str_equal_str_id' if dat['id_str']==str(dat['id']) else 'order_id_str_differs_str_id']+=1
     register('order_id_str',dat.get('id_str'),{'line':line_no,'event':ev,'field':'data.id_str','value':dat.get('id_str')})
     register('order_id_as_string',dat.get('id'),{'line':line_no,'event':ev,'field':'str(data.id)','value':None if dat.get('id') is None else str(dat['id'])})
     if snapshot is not None and next_order is None:next_order=ref
     previous=ref
    elif ch=='live_trades_btcusd' and ev=='trade':
     stats['trade_records']+=1
     for key in ('buy_order_id','sell_order_id'):register('trade_'+key,dat.get(key),{'line':line_no,'field':'data.'+key,'value':None if dat.get(key) is None else str(dat[key])})
    if line_no%512==0:check()
  if snapshot is None:raise RuntimeError('Expected snapshot not found')
  snapshot['next_order']=next_order
  sides=ids['snapshot_bids']|ids['snapshot_asks'];snapshot['cross_side_duplicate_count']=len(ids['snapshot_bids']&ids['snapshot_asks'])
  links={};witnesses=[]
  for kind in ('order_id_str','order_id_as_string','trade_buy_order_id','trade_sell_order_id'):
   matches=sides&ids[kind]
   links[kind]={'distinct_reference_ids':len(ids[kind]),'snapshot_intersection_distinct_ids':len(matches),
               'bids_intersection_distinct_ids':len(ids['snapshot_bids']&ids[kind]),'asks_intersection_distinct_ids':len(ids['snapshot_asks']&ids[kind])}
   for value in sorted(matches)[:3]:
    side='bids' if value in ids['snapshot_bids'] else 'asks';witnesses.append({'kind':kind,'snapshot_field':refs['snapshot_'+side][value],'equal_reference_field':refs[kind][value]})
  temporal={};snapref=snapshot['reference'];snapus=int(snapref['exchange_microtimestamp_exact'])
  for label,ref in (('previous_order',snapshot['previous_order']),('next_order',next_order)):
   if ref is None:temporal[label]='UNKNOWN_NO_ADJACENT_EVENT';continue
   temporal[label]={'snapshot_source_microtimestamp_relation_to_event_source_microtimestamp':relation(snapus,int(ref['exchange_microtimestamp_exact'])),
                    'snapshot_capture_time_relation_to_event_capture_time':relation(int(snapref['local_timestamp_100ns_epoch_ticks']),int(ref['local_timestamp_100ns_epoch_ticks']))}
  result={'status':'CACHED_IDENTITY_TIME_OBSERVED_NOT_QUEUE_AUTHENTICATION','source_sha256':EXPECTED,'source_line_count':line_no,'uncompressed_bytes_read':decoded,
          'timestamp_fraction_digit_counts':dict(fraction_digits),'time_representation':'source local prefix retained exactly; integer100ns ticks; native data.microtimestamp retained as source string/int microseconds; different clocks not treated as latency',
          'identity_statistics':dict(stats),'snapshot':snapshot,'id_equality_intersections':links,'temporal_relations':temporal,
          'scope_limit':'one cached minute; ID equality corroborates candidate semantics but does not independently certify official column meaning or complete FIFO/own fills',
          'no_snapshot_pointer_does_not_prove_no_possible_alignment':True,'financial_calculations':False}
  write('result.json',result);write('field-witnesses.json',{'source':str(SOURCE),'source_sha256':EXPECTED,'identity_equality_witnesses':witnesses,'snapshot_and_adjacent_times':{'snapshot':snapref,'previous_order':snapshot['previous_order'],'next_order':next_order},'prices_and_amounts_included':False})
  receipt['status']='PASS_NARROW_IDENTITY_TIME_CHECK'
 except BaseException as e:receipt.update(status='STOP_NO_RETRY',error_type=type(e).__name__,error_message=str(e))
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);check();receipt.update(utc_end=now(),wall_seconds=time.monotonic()-START,process_cpu_seconds=time.process_time()-CPU,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,threads_used=1,new_disk_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file()),download_bytes=0,payments=0,installs=0)
  write('check-receipt.json',receipt)
 print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
