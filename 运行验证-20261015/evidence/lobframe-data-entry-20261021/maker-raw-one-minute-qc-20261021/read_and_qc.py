"""One public unauthenticated HTTP GET; bounded structural QC only."""
import os,time
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
START=time.monotonic()
import json,hashlib,urllib.request,urllib.parse,urllib.error,signal,zlib,resource
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
R=Path(__file__).resolve().parent
CAP=4*1024*1024;UNCAP=16*1024*1024;DISK=32*1024*1024
FILTERS=[{'channel':'live_orders','symbols':['btcusd']},{'channel':'live_trades','symbols':['btcusd']}]
URL='https://api.tardis.dev/v1/data-feeds/bitstamp?'+urllib.parse.urlencode({'from':'2026-07-01T00:00:00.000Z','offset':0,'sliceSize':1,'filters':json.dumps(FILTERS,separators=(',',':'))})
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 with (R/p).open('x') as f:json.dump(x,f,ensure_ascii=True,indent=2);f.write('\n')
def hbytes(b):return hashlib.sha256(b).hexdigest()
def disk():return sum(p.stat().st_size for p in R.rglob('*') if p.is_file())
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def inflate(body):
 data=bytearray();remaining=body;members=0
 while remaining:
  dec=zlib.decompressobj(16+zlib.MAX_WBITS)
  part=dec.decompress(remaining,UNCAP-len(data))
  data.extend(part)
  if len(data)>=UNCAP:raise RuntimeError('Uncompressed cap reached; no further inflation')
  if not dec.eof:raise RuntimeError('gzip CRC/EOF incomplete or truncated')
  members+=1;remaining=dec.unused_data
 return bytes(data),members

def stamp(x):
 if not isinstance(x,str):raise ValueError('local timestamp not a string')
 d=datetime.fromisoformat(x.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError('local timestamp timezone missing')
 return d.astimezone(timezone.utc)

def qc(data):
 text=data.decode('utf-8');channels=Counter();events=Counter();formats=Counter();errors=Counter();orderfields=defaultdict(Counter);snapshots=[]
 keypaths=Counter();typemap=defaultdict(Counter);id_fields=Counter();tradelinks=Counter();chain=Counter();prior={};blanks=0;records=0;previous=None;first=None;last=None;outside=0;backwards=0
 window_start=stamp('2026-07-01T00:00:00.000Z');window_end=stamp('2026-07-01T00:01:00.000Z')
 def walk(x,path='',depth=0):
  if depth>8:return
  if isinstance(x,dict):
   for k,v in x.items():
    p=path+'.'+k if path else k;keypaths[p]+=1;typemap[p][type(v).__name__]+=1
    if k.lower().replace('_','') in ('id','orderid','buyorderid','sellorderid','eventid','preeventid'):id_fields[p]+=1
    if isinstance(v,dict):walk(v,p,depth+1)
    elif isinstance(v,list):
     for item in v:
      if isinstance(item,dict):walk(item,p+'[]',depth+1)
  # Numeric price/amount values are never converted, calculated or emitted.
 for line_no,line in enumerate(text.splitlines(),1):
  if not line.strip():blanks+=1;prior.clear();continue
  try:
   if line.startswith('{'):
    obj=json.loads(line);local=obj.get('localTimestamp',obj.get('local_timestamp'));msg=obj.get('message',obj);formats['json_envelope']+=1
   else:
    local,payload=line.split(' ',1);msg=json.loads(payload);formats['ISO_timestamp_space_native_JSON']+=1
   dt=stamp(local)
   if not isinstance(msg,dict):raise ValueError('Native object not dictionary')
  except Exception as e:errors[type(e).__name__]+=1;continue
  records+=1
  if first is None:first=dt
  if previous is not None and dt<previous:backwards+=1
  previous=dt;last=dt
  if not window_start<=dt<window_end:outside+=1
  ch=msg.get('channel','UNKNOWN');ev=msg.get('event','UNKNOWN')
  if not isinstance(ch,str):ch='NONSTRING_CHANNEL'
  if not isinstance(ev,str):ev='NONSTRING_EVENT'
  channels[ch]+=1;events[ch+'|'+ev]+=1;walk(msg)
  dat=msg.get('data');ds=dat if isinstance(dat,dict) else {}
  if ch=='live_orders_btcusd':
   for k in ds:orderfields[ev][k]+=1
  if ch=='live_trades_btcusd':
   for k in ('id','buy_order_id','sell_order_id','buy_orderID','sell_orderID','order_id','event_id','pre_event_id'):
    if k in ds:tradelinks[k]+=1
  if ev=='snapshot':
   shape={'line':line_no,'channel':ch,'generated_present':'generated' in msg,'generated_is_true':msg.get('generated') is True,'data_type':type(dat).__name__,'data_keys':sorted(ds)}
   arrays={}
   for side in ('asks','bids','orders'):
    arr=ds.get(side)
    if isinstance(arr,list):
     arrays[side]={'entry_count':len(arr),'entry_types':dict(Counter(type(x).__name__ for x in arr)),
       'array_entry_width_counts':dict(Counter(str(len(x)) for x in arr if isinstance(x,list))),
       'dict_entry_keys':sorted({k for x in arr if isinstance(x,dict) for k in x}),
       'array_column_types':{str(i):dict(Counter(type(x[i]).__name__ for x in arr if isinstance(x,list) and len(x)>i)) for i in range(4)}}
   shape['arrays']=arrays;snapshots.append(shape)
  eventid=ds.get('event_id',msg.get('event_id'));pre=ds.get('pre_event_id',msg.get('pre_event_id'))
  if eventid is not None:chain['records_with_event_id']+=1
  if pre is not None:chain['records_with_pre_event_id']+=1
  if eventid is not None and pre is not None:
   if ch in prior:
    chain['adjacent_same_channel_links_compared']+=1
    chain['adjacent_links_equal' if pre==prior[ch] else 'adjacent_links_different']+=1
   prior[ch]=eventid
 if sum(errors.values()):status='FAIL_RECORD_PARSE'
 elif records==0:status='FAIL_NO_PARSED_RECORDS'
 else:status='STRUCTURAL_QC_OBSERVED_NOT_FEED_COMPLETENESS'
 return {'status':status,'records':records,'blank_disconnect_markers':blanks,'line_formats':dict(formats),'parse_errors':dict(errors),
  'first_local_timestamp':None if first is None else first.isoformat(),'last_local_timestamp':None if last is None else last.isoformat(),
  'backwards_local_timestamps':backwards,'outside_requested_local_window':outside,'channels':dict(channels),'events':dict(events),
  'unexpected_channels':{k:v for k,v in channels.items() if k not in ('live_orders_btcusd','live_trades_btcusd')},
  'order_data_field_counts_by_event':{k:dict(v) for k,v in orderfields.items()},'trade_link_field_counts':dict(tradelinks),
  'id_field_path_presence_counts':dict(id_fields),'field_path_counts':dict(keypaths),'field_types':{k:dict(v) for k,v in typemap.items()},
  'snapshot_shapes':snapshots,'event_chain_descriptive_checks':dict(chain),
  'event_chain_semantics':'Only adjacent observed same-channel field equality after reset on disconnect; missing fields or unknown sequencing scope cannot prove continuity',
  'prices_quantities_ids_values_emitted':False,'financial_computations':False,'queue_FIFO_own_fills_profit':'UNKNOWN'}

def main():
 if (R/'get-started.json').exists():raise RuntimeError('One-GET marker exists; never retry')
 spec=json.loads((R/'read-spec.json').read_text())
 if spec['url']!=URL:raise RuntimeError('Frozen read-spec mismatch')
 write('get-started.json',{'utc':now(),'url':URL,'method':'GET','authenticated':False,'attempt':1,'pid':os.getpid(),'script_sha256':hbytes(Path(__file__).read_bytes())})
 receipt={'utc_start':now(),'url':URL,'method':'GET','authenticated':False,'attempts':1,'redirects_followed':0,'compressed_cap_bytes':CAP,'uncompressed_cap_bytes':UNCAP,'request_headers':{'Accept-Encoding':'gzip'},'actual_model':'UNKNOWN','actual_effort':'UNKNOWN'}
 body=bytearray();response=None;cpu=time.process_time()
 try:
  def alarm(*_):raise TimeoutError('60 second total network cap')
  signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,60)
  opener=urllib.request.build_opener(NoRedirect())
  req=urllib.request.Request(URL,headers={'Accept-Encoding':'gzip'},method='GET')
  response=opener.open(req,timeout=60)
  receipt.update(http_status=response.status,response_headers=dict(response.headers.items()),final_url=response.geturl())
  if response.status!=200:raise RuntimeError('Non200 HTTP; stop')
  encoding=response.headers.get('Content-Encoding','').strip().lower();receipt['content_encoding']=encoding
  if encoding not in ('gzip','identity'):raise RuntimeError('Content-Encoding not explicitly gzip/identity')
  length=response.headers.get('Content-Length');declared=int(length) if length is not None else None
  if declared is not None and declared>CAP:raise RuntimeError('Declared compressed Content-Length exceeds cap')
  with (R/'raw-response.bin').open('xb') as out:
   while True:
    if len(body)==CAP:
     if declared==CAP:break
     raise RuntimeError('Compressed cap reached; stopping without another read')
    chunk=response.read(min(65536,CAP-len(body)))
    if not chunk:break
    body.extend(chunk);out.write(chunk)
    if disk()>DISK:raise RuntimeError('New disk cap exceeded')
  if declared is not None and len(body)!=declared:raise RuntimeError('HTTP body length incomplete')
  receipt['network_body_complete']=True
  signal.setitimer(signal.ITIMER_REAL,0)
  if encoding=='gzip':decoded,members=inflate(bytes(body));receipt.update(gzip_eof_crc_verified=True,gzip_members=members)
  else:decoded=bytes(body);receipt['gzip_eof_crc_verified']='NOT_APPLICABLE_IDENTITY'
  receipt['uncompressed_bytes']=len(decoded)
  if len(decoded)>UNCAP:raise RuntimeError('Uncompressed cap exceeded')
  q=qc(decoded);write('qc.json',q);receipt['status']=q['status'];receipt['decoded_sha256']=hbytes(decoded)
 except BaseException as exc:
  receipt.update(status='STOP_NO_RETRY',error_type=type(exc).__name__,error_message=str(exc))
  if isinstance(exc,urllib.error.HTTPError):receipt.update(http_status=exc.code,response_headers=dict(exc.headers.items()))
 finally:
  signal.setitimer(signal.ITIMER_REAL,0)
  if response is not None:response.close()
  if not (R/'raw-response.bin').exists() and body:(R/'raw-response.bin').write_bytes(body)
  receipt.update(utc_end=now(),body_bytes_received=len(body),raw_sha256=hbytes(body),wall_seconds=time.monotonic()-START,process_cpu_seconds=time.process_time()-cpu,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,new_disk_bytes=disk(),threads_used=1,payments=0,installs=0,registrations=0)
  write('read-receipt.json',receipt)
 print(json.dumps({k:receipt.get(k) for k in ('status','http_status','body_bytes_received','uncompressed_bytes','raw_sha256','wall_seconds','process_cpu_seconds','peak_rss_bytes')}),flush=True)
if __name__=='__main__':main()
