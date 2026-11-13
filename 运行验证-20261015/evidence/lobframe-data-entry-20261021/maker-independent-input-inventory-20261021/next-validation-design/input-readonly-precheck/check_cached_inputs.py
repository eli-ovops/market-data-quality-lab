"""One bounded read-only cache QC; no orders, labels, returns or PnL."""
import os,time,signal,resource,json,gzip,csv,hashlib,calendar,re,math,bisect,sys
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
from collections import Counter
OUT=Path(__file__).resolve().parent
UNIT=OUT.parent.parent/'execution-20261022'; OWNER=UNIT/'owner'
BASE=UNIT.parent.parent
T=10_000_000; END=32452*T; TERM=32451*T
WALL=time.monotonic(); CPU=time.process_time(); MEM=256*1024**2; LIMIT=4*1024**2

def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def save(name,x):
 s=json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
 if len(s.encode())+sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())>LIMIT:raise RuntimeError('Output cap')
 with (OUT/name).open('x') as f:f.write(s)
def guard(*args):
 if time.monotonic()-WALL>60 or time.process_time()-CPU>60:raise TimeoutError('60s cap')
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>MEM:raise MemoryError('256MiB RSS cap')
def cap(s):
 m=re.fullmatch(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{7})Z',s)
 if not m:raise ValueError('Not exact seven digit UTC')
 return calendar.timegm(datetime.strptime(m[1],'%Y-%m-%dT%H:%M:%S').timetuple())*T+int(m[2])
def text(t):
 z,r=divmod(t,T);return datetime.fromtimestamp(z,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')+f'.{r:07d}Z'
def number(x,positive=False):
 d=Decimal(str(x))
 if not d.is_finite() or (d<=0 if positive else d<0):raise ValueError('Invalid nonfinite/negative field')
 return d
class Clock:
 def __init__(self):self.n=0;self.prev=None;self.gcd=0;self.delta_gcd=0;self.lastdigits=Counter();self.regressions=0;self.diffmin=None;self.diffmax=None;self.diffsign=Counter()
 def add(self,src,capture):
  self.n+=1;self.gcd=math.gcd(self.gcd,abs(src));self.lastdigits[str(src%1000)]+=1
  if self.prev is not None:
   self.delta_gcd=math.gcd(self.delta_gcd,abs(src-self.prev));self.regressions+=src<self.prev
  self.prev=src;d=capture-src*10;self.diffmin=d if self.diffmin is None else min(d,self.diffmin);self.diffmax=d if self.diffmax is None else max(d,self.diffmax);self.diffsign['positive' if d>0 else 'negative' if d<0 else 'zero']+=1
 def result(self):return {'records':self.n,'source_integer_microsecond_values_gcd':self.gcd,'successive_source_differences_gcd_us':self.delta_gcd,'source_us_mod1000_counts':dict(self.lastdigits),'source_regressions':self.regressions,'capture_minus_source_min_100ns_ticks':self.diffmin,'capture_minus_source_max_100ns_ticks':self.diffmax,'capture_minus_source_sign_counts':dict(self.diffsign),'interpretation':'Observed numerical lattice only; not clock accuracy or user/network latency'}
def normalized(day,cut):
 with gzip.open(OWNER/'data'/f'{day}-trades.jsonl.gz','rt') as f:
  for line in f:
   r=json.loads(line)
   if r[0]>cut:break
   yield r

def raw_day(day,begin,ledger):
 cut=begin+END;it=iter(normalized(day,cut));clock=Clock();counts=Counter();ids=set();inputs=[];capture_mod=Counter();first=None;last=None;lastcap=-1
 for offset in range(0,541,10):
  rec=next(x for x in ledger if x['day']==day and x['offset_minutes']==offset);p=Path(rec['path']);digest=sha(p)
  if digest!=rec['sha256']:raise ValueError('Raw compressed identity mismatch')
  inputs.append({'path':str(p),'sha256':digest,'bytes':p.stat().st_size,'offset_minutes':offset})
  with gzip.open(p,'rb') as f:
   for line in f:
    if not line.strip():counts['disconnect_markers']+=1;continue
    stamp,payload=line.decode().rstrip('\r\n').split(' ',1);c=cap(stamp)
    if c>cut:break
    if c<lastcap or not begin<=c<begin+86400*T:raise ValueError('Raw capture/day order')
    lastcap=c;first=c if first is None else first;last=c;capture_mod[str(c%10)]+=1
    m=json.loads(payload,parse_float=Decimal);d=m.get('data',{})
    if m.get('channel')!='live_trades_btcusd':raise ValueError('Wrong raw channel')
    counts[str(m.get('event'))]+=1
    if m.get('event')!='trade':continue
    for k in ('id','buy_order_id','sell_order_id','microtimestamp'):
     if not str(d.get(k,'')).isdigit():raise ValueError('Missing integer identity/source')
    if type(d.get('type')) is not int or d['type'] not in (0,1):raise ValueError('Trade type')
    ident=int(d['id'])
    if ident in ids:raise ValueError('Duplicate trade ID')
    ids.add(ident);src=int(d['microtimestamp']);clock.add(src,c)
    a=number(d.get('amount_str',d.get('amount')),True);pr=number(d.get('price_str',d.get('price')),True)
    if 'amount_str' in d and 'amount' in d and a!=number(d['amount'],True):raise ValueError('amount_str vs numeric mismatch')
    if 'price_str' in d and 'price' in d and pr!=number(d['price'],True):raise ValueError('price_str vs numeric mismatch')
    n=next(it,None)
    if n is None or n[:6]!=[c,src,ident,int(d['buy_order_id']),int(d['sell_order_id']),d['type']] or Decimal(n[6])!=pr or n[7]!=offset:raise ValueError('Raw/normalized identity/value mismatch')
    counts['raw_normalized_exact_match']+=1;counts['valid_positive_amount']+=1
    if counts['trade']%1000==0:guard()
  guard()
 if next(it,None) is not None:raise ValueError('Extra normalized prefix trade')
 if counts['disconnect_markers']:raise ValueError('Unexpected explicit prefix disconnect; fixed window unchanged')
 return {'counts':dict(counts),'first_capture':text(first),'last_capture':text(last),'capture_100ns_mod10_counts':dict(capture_mod),'clock':clock.result(),'quantity_unit':{'raw_scalar_fields_verified':True,'amount_str_numeric_equality':True,'normalized_contains_amount':False,'BTC_unit_certified_by_this_QC':False,'unit_status':'UNKNOWN: field values cannot certify units; model proposal labels BTC, separate official definition needed'},'raw_compressed_inputs':inputs,'prefix_only':'Terminal slice body read only through cutoff; full compressed identity hashed against sealed ledger. No fresh all-file gzip CRC claim.'}

def bbo_day(item,begin):
 cut=begin+END;groups=[];clock=Clock();n=0;previous=-1;maxsrc=-1;g=None;badrows=Counter();header=None
 def flush():
  if g is not None:groups.append((g['t'],g['src'],g['valid'],g['conflict'],g['regressed'],g['row']))
 with gzip.open(item['path'],'rt',newline='') as f:
  r=csv.DictReader(f);header=r.fieldnames
  fields=[f'{side}[{i}].{v}' for i in range(25) for side in ('asks','bids') for v in ('price','amount')]
  if set(header)!=set(['exchange','symbol','timestamp','local_timestamp']+fields) or len(header)!=104:raise ValueError('Snapshot schema')
  for row in r:
   t=int(row['local_timestamp'])*10
   if t>cut:break
   n+=1;src=int(row['timestamp']);clock.add(src,t)
   if row['exchange']!='bitstamp' or row['symbol']!='BTCUSD' or not begin<=t<begin+86400*T or t<previous:raise ValueError('BBO identity/day/capture ordering')
   previous=t;valid=True;values=()
   try:
    values=tuple(number(row[k],k.endswith('.price')) for k in fields)
    bids=[values[4*i+2] for i in range(25)];asks=[values[4*i] for i in range(25)]
    if any(bids[i]<bids[i+1] or asks[i]>asks[i+1] for i in range(24)) or bids[0]>=asks[0]:raise ValueError('BBO ordering/cross')
   except (ValueError,ArithmeticError):valid=False;badrows['invalid_or_incomplete_25_levels']+=1
   reg=src<maxsrc;maxsrc=max(maxsrc,src)
   if g is not None and t==g['t']:
    g['conflict']|=values!=g['values'];g['valid']&=valid;g['regressed']|=reg;g['src']=src;g['row']=n
   else:
    flush();g={'t':t,'src':src,'valid':valid,'conflict':False,'regressed':reg,'row':n,'values':values}
   if n%1000==0:guard()
 flush();caps=[x[0] for x in groups]
 def eligibility(g,q,equal=False):
  if g is None:return 'no_reference'
  t,src,valid,conflict,reg,row=g
  if not (t<=q if equal else t<q):return 'capture_not_before'
  if src*10>=q:return 'source_not_before'
  if q-t>T:return 'age_over_1s'
  if not valid:return 'invalid_25_levels'
  if conflict:return 'same_capture_conflict'
  if reg:return 'source_regression'
  return 'valid'
 checks={}
 for delay in (0,T//10,T//2):
  counts=Counter();firstvalid=None;lastvalid=None
  for sec in range(5,32450):
   q=begin+sec*T+delay;j=bisect.bisect_left(caps,q)-1;g0=groups[j] if j>=0 else None;reason=eligibility(g0,q);counts[reason]+=1
   if reason=='valid':firstvalid=q if firstvalid is None else firstvalid;lastvalid=q
  checks[str(delay//10000)+'ms']={'checkpoints':sum(counts.values()),'counts':dict(counts),'first_valid_checkpoint':text(firstvalid) if firstvalid else None,'last_valid_checkpoint':text(lastvalid) if lastvalid else None}
 q=begin+TERM;j=bisect.bisect_left(caps,q)-1;g0=groups[j] if j>=0 else None;initial_reason=eligibility(g0,q);selected=None
 if initial_reason=='valid':selected=(g0,q,'strict_asof_at_09:00:51')
 else:
  for gg in groups[bisect.bisect_left(caps,q):]:
   if gg[0]>cut:break
   if eligibility(gg,gg[0],True)=='valid':selected=(gg,gg[0],'first_complete_arriving_reference_in_fixed_terminal_window');break
 terminal={'initial_09:00:51_reason':initial_reason,'exists':selected is not None,'no_price_or_return_output':True}
 if selected:
  gg,e,how=selected;terminal.update(selection=how,evaluation_time=text(e),reference_capture=text(gg[0]),reference_source_us=gg[1],reference_source_time=text(gg[1]*10),row_in_original_file=gg[5],capture_age_ticks=e-gg[0],all25levels_valid=True)
 return {'input_path':item['path'],'input_sealed_compressed_sha256':item['compressed_sha256'],'large_compressed_hash_not_recomputed':True,'full_day_EOF_CRC_not_rerun':True,'prefix_rows':n,'capture_groups':len(groups),'same_capture_conflicting_groups':sum(g[3] for g in groups),'invalid_groups':sum(not g[2] for g in groups),'regressed_source_groups':sum(g[4] for g in groups),'row_issues':dict(badrows),'clock':clock.result(),'asof_checks':checks,'terminal_reference':terminal}

def main():
 if (OUT/'started.json').exists():raise RuntimeError('Single attempt already started')
 resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,1,1)
 spec={'status':'METHOD_FIXED_BEFORE_READ','days':['2026-05-01','2026-06-01'],'prefix':'UTC00:00:00 through09:00:52 inclusive, warmup included','checkpoints':'00:00:05..09:00:49 inclusive each nominal integer second plus0/100/500ms','reference_rule':'last nominal capture strictly before checkpoint; source strictly before; age<=1s; full100 decimal price/amount fields finite (prices>0 amounts>=0), bid<ask and sorted; group conflicts/regressions invalid; no fallback','terminal':'At09:00:51 use same strict asof rule; else first valid complete arriving group through09:00:52 inclusive (capture equal arrival allowed only terminal observation), no price choice','clock':'capture-source difference and source numeric lattice only, not clock accuracy/latency','units':'No physical unit inferred from numeric values','limits':{'CPU_seconds':60,'wall_seconds':60,'RSS_bytes':MEM,'new_output_bytes':LIMIT,'threads':1},'prohibited_outputs':['virtual orders','fills','inventory','signals','labels','returns','PnL'],'script_sha256':sha(__file__),'actual_model_effort':'UNKNOWN'}
 save('method-spec.json',spec);save('started.json',{'utc':utc(),'pid':os.getpid(),'script_sha256':spec['script_sha256'],'executable':sys.executable,'version':sys.version,'network':0,'input_ledger_sha256':sha(OWNER/'GET-ledger.jsonl')})
 try:
  ledger=[json.loads(x) for x in (OWNER/'GET-ledger.jsonl').read_text().splitlines()];receipt=json.loads((BASE/'execution-20261021/data-receipt.json').read_text());days=[]
  for day in spec['days']:
   begin=calendar.timegm(datetime.strptime(day,'%Y-%m-%d').timetuple())*T
   item=next(x for x in receipt['files'] if x['date']==day)
   days.append({'date':day,'raw':raw_day(day,begin,ledger),'snapshot25':bbo_day(item,begin)})
   guard()
  status='READONLY_INPUT_QC_COMPLETE_NOT_ECONOMIC_VALIDATION';save('summary.json',{'status':status,'days':days,'network':0,'prices_quantities_values_emitted':False,'no_orders_fills_positions_PnL':True});error=None
 except BaseException as exc:
  status='QC_FAILED_STOP_NO_RETRY';error={'type':type(exc).__name__,'message':str(exc)}
 finally:
  signal.setitimer(signal.ITIMER_REAL,0)
  save('completion-receipt.json',{'status':status,'utc':utc(),'error':error,'script_sha256':sha(__file__),'CPU_seconds':time.process_time()-CPU,'wall_seconds':time.monotonic()-WALL,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'threads':1,'network':0,'output_bytes_before_receipt':sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()),'actual_model_effort':'UNKNOWN'})
 print(json.dumps({'status':status,'error':error,'output':str(OUT)},ensure_ascii=False))
 if error:sys.exit(1)
if __name__=='__main__':main()
