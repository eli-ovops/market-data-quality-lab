"""Read only frozen cached sources, never network. Compact exact 12-place integers."""
import gzip,csv,json,hashlib,calendar,re,bisect,array
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from core import Trade,T,SCALE,decimal_int

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def cap(s):
 m=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)\.(\d{7})Z',s)
 if not m:raise ValueError('Exact7digitUTC required')
 return calendar.timegm(datetime.strptime(m[1],'%Y-%m-%dT%H:%M:%S').timetuple())*T+int(m[2])
def day0(day):return calendar.timegm(datetime.strptime(day,'%Y-%m-%d').timetuple())*T

def integer_value(s,price=False):
 d=Decimal(s)
 if not d.is_finite() or (d<=0 if price else d<0):raise ValueError('Invalid field')
 tup=d.as_tuple();digits=tup.digits;shift=tup.exponent+12
 coeff=int(''.join(str(x) for x in digits))
 if shift>=0:
  if coeff and len(digits)+shift>19:raise ValueError('Fixed point overflow')
  n=coeff*10**shift if coeff else 0
 else:
  places=-shift
  if places>len(digits):
   if coeff:raise ValueError('More than12decimalplaces')
   n=0
  else:
   n,rem=divmod(coeff,10**places)
   if rem:raise ValueError('More than12decimalplaces')
 if not 0<=n<2**63:raise ValueError('Fixed point overflow')
 return n

class Quotes:
 def __init__(self):
  self.cap=array.array('q');self.src=array.array('q');self.row=array.array('I');self.bad=array.array('B');self.values=array.array('q');self.meta={}
 def book(self,j):return self.values[j*100:(j+1)*100]
 def ref(self,t,equal=False):
  j=(bisect.bisect_right(self.cap,t) if equal else bisect.bisect_left(self.cap,t))-1
  if j<0 or self.bad[j] or self.src[j]*10>=t or t-self.cap[j]>T:return None
  return int(self.row[j]),self.book(j)
 def terminal(self,t,last):
  got=self.ref(t)
  if got:return t,got
  j=bisect.bisect_left(self.cap,t)
  while j<len(self.cap) and self.cap[j]<=last:
   tt=self.cap[j]
   if not self.bad[j] and self.src[j]*10<tt:return tt,(int(self.row[j]),self.book(j))
   j+=1
  return None

def load_quotes(item,start,budget):
 p=Path(item['path']);st=p.stat()
 if st.st_size!=item['stat_size'] or st.st_mtime_ns!=item['stat_mtime_ns']:raise ValueError('BBO stat identity drift')
 q=Quotes();prev=-1;maxsrc=-1;g=None;n=0
 def flush():
  if g is not None:
   q.cap.append(g[0]);q.src.append(g[1]);q.row.append(g[2]);q.bad.append(g[4]);q.values.extend(g[3])
 fields=[f'{side}[{i}].{v}' for i in range(25) for side in ('asks','bids') for v in ('price','amount')]
 with gzip.open(p,'rt',newline='') as f:
  reader=csv.DictReader(f)
  if len(reader.fieldnames)!=104 or set(reader.fieldnames)!=set(['exchange','symbol','timestamp','local_timestamp']+fields):raise ValueError('Snapshot schema drift')
  for n,r in enumerate(reader,1):
   t=int(r['local_timestamp'])*10
   if t>start+32452*T:break
   if r['exchange']!='bitstamp' or r['symbol']!='BTCUSD' or not start<=t<start+86400*T or t<prev:raise ValueError('BBO identity/time')
   src=int(r['timestamp']);vals=tuple(integer_value(r[k],k.endswith('.price')) for k in fields)
   if vals[2]>=vals[0] or any(vals[4*i]>vals[4*(i+1)] or vals[4*i+2]<vals[4*(i+1)+2] for i in range(24)):raise ValueError('BBO price ordering')
   bad=src<maxsrc;maxsrc=max(src,maxsrc)
   if g is not None and t==g[0]:g=(t,src,n,vals,g[4] or bad or vals!=g[3])
   else:flush();g=(t,src,n,vals,bad)
   prev=t
   if n%1000==0:budget.guard()
 flush();q.meta={'prefix_groups':len(q.cap),'invalid_conflict_groups':sum(q.bad),'input_path':str(p),'large_file_hash_not_rerun':True,'old_full_CRC_not_rerun':True}
 return q

def load_trades(records,start,budget):
 trades=[];ids=set();prev=-1
 for rec in records:
  p=Path(rec['path'])
  if sha(p)!=rec['sha256']:raise ValueError('Raw compressed identity drift')
  with gzip.open(p,'rt') as f:
   for line_no,line in enumerate(f,1):
    if not line.strip():raise ValueError('Unexpected prefix disconnect')
    stamp,payload=line.rstrip('\r\n').split(' ',1);t=cap(stamp)
    if t>start+32452*T:break
    if t<prev or not start<=t<start+86400*T:raise ValueError('Raw capture/day ordering')
    prev=t;x=json.loads(payload,parse_float=Decimal)
    if x.get('channel')!='live_trades_btcusd':raise ValueError('Wrong raw channel')
    if x.get('event')!='trade':continue
    d=x['data'];ident=int(d['id']);src=int(d['microtimestamp'])
    if ident in ids:raise ValueError('Duplicate raw tradeID')
    ids.add(ident)
    if type(d['type']) is not int or d['type'] not in (0,1):raise ValueError('Type not0/1')
    for name in ('buy_order_id','sell_order_id','microtimestamp','id'):
     if not str(d[name]).isdigit():raise ValueError('Missing trade identity')
    price=Decimal(str(d.get('price_str',d['price'])));qty=Decimal(str(d.get('amount_str',d['amount'])))
    if not price.is_finite() or not qty.is_finite() or price<=0 or qty<=0:raise ValueError('Invalid trade price/amount')
    if price!=Decimal(str(d['price'])) or qty!=Decimal(str(d['amount'])):raise ValueError('Raw double-encoding mismatch')
    integer_value(str(price),True);integer_value(str(qty),True)
    trades.append(Trade(t,src,ident,d['type'],price,qty,rec['offset_minutes'],line_no))
  budget.guard()
 return trades

def score_at(t,trades,caps):
 def ambiguous(boundary):
  j=bisect.bisect_left(caps,boundary-1)
  return j<len(caps) and caps[j]-1<boundary<=caps[j]+1
 if ambiguous(t-T) or ambiguous(t):return 0,True,'capture_boundary_uncertain'
 a=bisect.bisect_left(caps,t-T);b=bisect.bisect_left(caps,t)
 buy=sum(x.typ==0 for x in trades[a:b]);n=b-a
 return (1 if 2*buy>n else -1 if 2*buy<n else 0),False,('no_score' if not n else 'zero' if 2*buy==n else 'nonzero')
