"""Independent two-day fixed flow challenge. Standard library, no fitted model."""
import os,time
PROCESS_START=time.monotonic();CPU_START=time.process_time()
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import array,bisect,calendar,csv,gzip,hashlib,io,json,math,random,re,resource,signal,urllib.request,urllib.parse,urllib.error
from collections import Counter,defaultdict
from datetime import datetime,timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from dataclasses import dataclass
OWNER=Path(__file__).resolve().parent
ROOT=OWNER.parent
BASE=ROOT.parent.parent
PLAN=ROOT.parent/'\u4e24\u65e5\u6210\u4ea4\u6d41\u5386\u53f2\u6311\u6218-\u5b8c\u6574\u5355\u5143\u63d0\u6848-\u672a\u6267\u884c.md'
PLAN_SHA='39b9b801e57404b2c5cd48b5e7bb6ea4d53e1ae301f724c487904db3bb90b5ea'
DATES=('2026-05-01','2026-06-01')
TICK=10_000_000
MEM=536870912;DISK=268435456;DOWNLOAD=67108864
DEADLINE=datetime(2026,10,22,1,59,57,tzinfo=timezone.utc).timestamp()

def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()
def write_new(path,x):
 with Path(path).open('x') as f:json.dump(x,f,ensure_ascii=True,indent=2,allow_nan=False);f.write('\n')
def append(path,x):
 with Path(path).open('a') as f:f.write(json.dumps(x,ensure_ascii=True,separators=(',',':'),allow_nan=False)+'\n')
def disk():
 total=0
 for p in OWNER.rglob('*'):
  if p.is_symlink():raise RuntimeError('Output symlink forbidden')
  if p.is_file():total+=p.stat().st_size
 return total

def prior_resources():
 sums=Counter()
 for p in OWNER.glob('resource-*.json'):
  v=json.loads(p.read_text())
  for k in ('compute_seconds','network_seconds','wait_seconds','download_bytes','GET_attempts'):sums[k]+=v.get(k,0)
 return sums

class Budget:
 def __init__(self,phase):
  self.phase=phase;self.start=PROCESS_START;self.cpu_start=CPU_START;self.prior=prior_resources();self.net=0.;self.wait=0.;self.net_start=None;self.bytes=0;self.gets=0
  signal.signal(signal.SIGALRM,self.alarm);self.arm();self.guard()
 def compute(self):return time.monotonic()-self.start-self.net-self.wait-(time.monotonic()-self.net_start if self.net_start is not None else 0)
 def guard(self):
  current_net=self.net+(time.monotonic()-self.net_start if self.net_start is not None else 0)
  if time.time()>=DEADLINE:raise TimeoutError('Active deadline')
  if self.prior['compute_seconds']+self.compute()>1800:raise TimeoutError('Cumulative compute cap')
  if self.prior['network_seconds']+current_net>1800:raise TimeoutError('Cumulative network cap')
  if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>MEM:raise MemoryError('RSS cap')
  if disk()>DISK:raise RuntimeError('Disk cap')
  if self.prior['download_bytes']+self.bytes>DOWNLOAD or self.prior['GET_attempts']+self.gets>288:raise RuntimeError('Download/GET cap')
 def alarm(self,*_):self.guard();self.arm()
 def arm(self):
  remaining=min(DEADLINE-time.time(),1800-self.prior['compute_seconds']-self.compute())
  if self.net_start is not None:remaining=min(remaining,1800-self.prior['network_seconds']-self.net-(time.monotonic()-self.net_start))
  signal.setitimer(signal.ITIMER_REAL,max(.001,min(1.,remaining)))
 def begin_network(self):self.guard();self.net_start=time.monotonic();self.gets+=1;self.arm()
 def end_network(self):
  if self.net_start is not None:self.net+=time.monotonic()-self.net_start;self.net_start=None
  self.guard();self.arm()
 def pause(self,seconds):
  self.guard();start=time.monotonic()
  # Mark waiting in advance so the periodic guard does not charge sleep as compute.
  self.wait+=seconds
  try:time.sleep(seconds)
  finally:self.wait+=time.monotonic()-start-seconds
  self.guard()
 def finish(self,status):
  if self.net_start is not None:self.net+=time.monotonic()-self.net_start;self.net_start=None
  signal.setitimer(signal.ITIMER_REAL,0)
  rec={'phase':self.phase,'status':status,'utc':now(),'pid':os.getpid(),'compute_seconds':max(0.,self.compute()),'network_seconds':self.net,'wait_seconds':self.wait,
       'wall_seconds':time.monotonic()-self.start,'CPU_seconds':time.process_time()-self.cpu_start,'download_bytes':self.bytes,'GET_attempts':self.gets,
       'prior':dict(self.prior),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'new_disk_bytes':disk(),'threads_used':1,'actual_model':'UNKNOWN','actual_effort':'UNKNOWN'}
  rec['cumulative_compute_seconds']=self.prior['compute_seconds']+rec['compute_seconds'];rec['cumulative_network_seconds']=self.prior['network_seconds']+self.net
  write_new(OWNER/f'resource-{self.phase}-{time.time_ns()}.json',rec);return rec


def day0(day):return calendar.timegm(datetime.strptime(day,'%Y-%m-%d').timetuple())*TICK

def capture(text):
 m=re.fullmatch(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{7})Z',text)
 if not m:raise ValueError('Native capture requires exact7digit UTC')
 return calendar.timegm(datetime.strptime(m[1],'%Y-%m-%dT%H:%M:%S').timetuple())*TICK+int(m[2])

def positive_text(value):
 x=Decimal(str(value))
 if not x.is_finite() or x<=0:raise ValueError('Nonpositive/nonfinite price or amount')
 return str(x)

def cache_inputs():
 r=json.loads((BASE/'execution-20261021/data-receipt.json').read_text());out=[];allowed=BASE/'execution-20261021/data'
 for day in DATES:
  matches=[x for x in r['files'] if x['date']==day]
  if len(matches)!=1:raise RuntimeError('Cache identity missing')
  x=matches[0];p=Path(x['path'])
  if not p.is_relative_to(allowed):raise RuntimeError('Cache outside allowed project data')
  q=p
  while q!=BASE:
   if q.is_symlink():raise RuntimeError('Cache symlink forbidden')
   q=q.parent
  if p.resolve(strict=True)!=p:raise RuntimeError('Cache resolved elsewhere')
  out.append({'date':day,'path':str(p),'sha256':x['compressed_sha256'],'rows':x['rows']})
 return out

def inspect_cache(item,budget):
 if sha(item['path'])!=item['sha256']:raise RuntimeError('Cache hash mismatch')
 start=day0(item['date']);previous=None;src_prev=None;rows=0
 with gzip.open(item['path'],'rt',newline='') as f:
  reader=csv.DictReader(f);header=reader.fieldnames
  required=['exchange','symbol','timestamp','local_timestamp']+[f'{s}[{i}].{v}' for i in range(25) for s in ('asks','bids') for v in ('price','amount')]
  if len(header)!=len(set(header)) or set(header)!=set(required):raise RuntimeError('Snapshot25 schema mismatch')
  for row in reader:
   rows+=1;t=int(row['local_timestamp'])*10;src=int(row['timestamp'])*10
   if row['exchange']!='bitstamp' or row['symbol']!='BTCUSD' or not start<=t<start+86400*TICK:raise RuntimeError('Cache object/day mismatch')
   if previous is not None and (t<previous or src<src_prev):raise RuntimeError('Cache time regression')
   previous=t;src_prev=src
   if rows%10000==0:budget.guard()
 if rows!=item['rows']:raise RuntimeError('Cache row count mismatch')
 return {**item,'actual_sha256':item['sha256'],'gzip_EOF_CRC':True,'schema_identity_UTC_order_rows':True,'economic_labels_calculated':False}

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def url(day,offset):
 return 'https://api.tardis.dev/v1/data-feeds/bitstamp?'+urllib.parse.urlencode({'from':day+'T00:00:00.000Z','offset':offset,'sliceSize':10,'filters':json.dumps([{'channel':'live_trades','symbols':['btcusd']}],separators=(',',':'))})


def download_piece(day,offset,budget):
 dest=OWNER/'data'/day/f'{offset:04d}.bin';dest.parent.mkdir(exist_ok=True)
 rec={'day':day,'offset_minutes':offset,'sliceSize':10,'url':url(day,offset),'utc_start':now(),'request_headers':{'Accept-Encoding':'gzip'},'attempt':budget.gets+1,'authenticated':False,'redirects_followed':0,'path':str(dest)}
 budget.begin_network();response=None;length=None;received=0;h=hashlib.sha256()
 try:
  remain=min(60.,1800-budget.prior['network_seconds']-budget.net,DEADLINE-time.time())
  response=urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(rec['url'],headers={'Accept-Encoding':'gzip'},method='GET'),timeout=max(.1,remain))
  rec.update(http_status=response.status,response_headers=dict(response.headers.items()),final_url=response.geturl())
  if response.status!=200:raise RuntimeError('Non200 source response')
  expected_name='bitstamp/'+day.replace('-','/')+f'/{offset//60:02d}/{offset%60:02d}'
  if response.headers.get('x-name') is not None and response.headers.get('x-name')!=expected_name:raise RuntimeError('Source x-name identity mismatch')
  enc=response.headers.get('Content-Encoding','identity').strip().lower();rec['effective_encoding']=enc
  if enc not in ('gzip','identity'):raise RuntimeError('Unsupported Content-Encoding')
  length=response.headers.get('Content-Length');length=int(length) if length is not None else None
  cap=DOWNLOAD-budget.prior['download_bytes']-budget.bytes
  if length is not None and length>cap:raise RuntimeError('Declared body exceeds remaining total download cap')
  with dest.open('xb') as f:
   while True:
    remaining=DOWNLOAD-budget.prior['download_bytes']-budget.bytes
    if remaining<=0:
     if length==received:break
     raise RuntimeError('Total compressed cap reached')
    part=response.read(min(65536,remaining))
    if not part:break
    f.write(part);h.update(part);received+=len(part);budget.bytes+=len(part);budget.guard()
  if length is not None and received!=length:raise RuntimeError('Incomplete HTTP body')
  rec.update(body_complete=True,bytes=received,sha256=h.hexdigest())
 except BaseException as exc:
  rec.update(body_complete=False,bytes=received,sha256=h.hexdigest(),error_type=type(exc).__name__,error_message=str(exc))
  if isinstance(exc,urllib.error.HTTPError):rec.update(http_status=exc.code,response_headers=dict(exc.headers.items()))
  raise
 finally:
  if response is not None:response.close()
  try:budget.end_network()
  finally:rec['utc_end']=now();append(OWNER/'GET-ledger.jsonl',rec)
 return rec

@dataclass(slots=True)
class Trade:
 cap:int;src:int;id:int;buy:int;sell:int;typ:int;price:str;slice:int;line:int


def parse_piece(rec,daystate,normalized,budget):
 day=rec['day'];lo=day0(day)+rec['offset_minutes']*60*TICK;hi=lo+600*TICK;counts=Counter();first=None;last=None
 opener=gzip.open if rec['effective_encoding']=='gzip' else open
 with opener(rec['path'],'rb') as f:
  for linenum,line in enumerate(f,1):
   if len(line)>1024*1024:raise RuntimeError('Oversized filtered trade record')
   if not line.strip():daystate['pending_gap']=True;counts['disconnect_markers']+=1;continue
   text,payload=line.decode('utf-8').rstrip('\r\n').split(' ',1);cap=capture(text);msg=json.loads(payload);dat=msg.get('data',{})
   if not lo<=cap<hi:raise RuntimeError('Raw slice capture outside fixed10minutes')
   if cap<daystate['last']:raise RuntimeError('Native capture regression')
   if first is None:first=cap
   if daystate['pending_gap']:
    daystate['gaps'].append([daystate['last'] if daystate['last']>=day0(day) else day0(day),cap]);daystate['pending_gap']=False
   daystate['last']=cap;last=cap
   if msg.get('channel')!='live_trades_btcusd':raise RuntimeError('Unexpected raw channel/object')
   ev=msg.get('event');counts[str(ev)]+=1
   if ev=='trade':
    if type(dat.get('type')) is not int or dat['type'] not in (0,1):raise RuntimeError('Unsupported raw trade type')
    for key in ('id','buy_order_id','sell_order_id'):
     if type(dat.get(key)) not in (int,str) or not str(dat[key]).isdigit():raise RuntimeError('Missing/bad trade/orderID')
    ident=int(dat['id'])
    if ident in daystate['ids']:raise RuntimeError('Duplicate tradeID')
    daystate['ids'].add(ident)
    src=str(dat.get('microtimestamp',''))
    if not src.isdigit():raise RuntimeError('Missing native source microtimestamp')
    price=positive_text(dat.get('price_str',dat.get('price')));positive_text(dat.get('amount_str',dat.get('amount')))
    record=[cap,int(src),ident,int(dat['buy_order_id']),int(dat['sell_order_id']),dat['type'],price,rec['offset_minutes'],linenum]
    normalized.write(json.dumps(record,separators=(',',':'))+'\n')
   if linenum%2000==0:budget.guard()
 rec_qc={'day':day,'offset_minutes':rec['offset_minutes'],'counts':dict(counts),'first_capture_ticks':first,'last_capture_ticks':last,'empty_slice':sum(counts.values())==0,'gzip_EOF_CRC':rec['effective_encoding']=='gzip','complete_identity_body':rec['effective_encoding']=='identity'}
 append(OWNER/'raw-QC-ledger.jsonl',rec_qc);return rec_qc


def acquire_all(budget):
 seals=[]
 for day in DATES:
  state={'last':day0(day)-1,'pending_gap':False,'gaps':[],'ids':set()};qcs=[];path=OWNER/'data'/f'{day}-trades.jsonl.gz'
  with gzip.open(path,'xt',encoding='utf-8') as normalized:
   for offset in range(0,1440,10):
    if budget.gets:budget.pause(1.)
    rec=download_piece(day,offset,budget);qcs.append(parse_piece(rec,state,normalized,budget))
    if (offset//10+1)%24==0:print(json.dumps({'event':'acquired','day':day,'pieces':offset//10+1,'utc':now()}),flush=True)
  if state['pending_gap']:state['gaps'].append([state['last'] if state['last']>=day0(day) else day0(day),day0(day)+86400*TICK])
  dayseal={'date':day,'pieces':144,'trade_count':len(state['ids']),'normalized_path':str(path),'normalized_sha256':sha(path),'disconnect_intervals_closed':state['gaps'],'slice_counts':qcs}
  write_new(OWNER/f'{day}-data-seal.json',dayseal);seals.append(dayseal)
 write_new(OWNER/'data-seal.json',{'utc':now(),'days':seals,'GET_ledger_sha256':sha(OWNER/'GET-ledger.jsonl'),'raw_QC_ledger_sha256':sha(OWNER/'raw-QC-ledger.jsonl')})
 return seals
