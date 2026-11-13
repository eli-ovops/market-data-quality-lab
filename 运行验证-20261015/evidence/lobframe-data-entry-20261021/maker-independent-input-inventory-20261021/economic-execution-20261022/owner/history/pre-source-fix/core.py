"""Independent fixed F/H conditional ledger. No network or account capabilities."""
from decimal import Decimal, getcontext, ROUND_DOWN
from dataclasses import dataclass
from collections import Counter
import hashlib, heapq
getcontext().prec=60
D=Decimal; ZERO=D(0); ONE=D(1); T=10_000_000; SCALE=10**12
MAKER=D('.003'); TAKER=D('.004'); SLIP=D('.0001')
QSTEP=D('0.000000000001')
def decimal_int(n):return D(n)/SCALE
def quantity(mid):return (D(50)/mid).quantize(QSTEP,rounding=ROUND_DOWN)
@dataclass(slots=True)
class Trade:
 cap:int; src:int; ident:int; typ:int; price:Decimal; qty:Decimal; offset:int=0; line:int=0
@dataclass(slots=True)
class Order:
 ident:int; side:str; price:Decimal; qty:Decimal; leaves:Decimal; submit:int
 state:str='pending'; accepted:int=0; ahead:Decimal=ZERO; cancel_at:int=0; cancel_sent:int=0; maxsrc:int=-1

def consume(a,r,v,cross=False):
 """A print's quantity is used once; crossing ignores old ahead by declared assumption."""
 if cross:return ZERO,min(r,v)
 used=min(a,v);return a-used,min(r,v-used)

def liquidation(q,book):
 """No order placed: exact hypothetical/terminal bid ladder, no repeated depth use."""
 if q==0:return ZERO,ZERO,[]
 rem=q;gross=ZERO;legs=[]
 for i in range(25):
  price,amount=decimal_int(book[4*i+2]),decimal_int(book[4*i+3])
  v=min(rem,amount)
  if v:
   px=price*(ONE-SLIP);notional=px*v;fee=notional*TAKER
   gross+=notional;legs.append((i,px,v,fee));rem-=v
  if rem==0:break
 if rem:raise ValueError('Insufficient25depth')
 return gross,gross*TAKER,legs

class NullLog:
 def write(self,*a,**kw):pass
class Engine:
 def __init__(self,policy,model,delay,q,quotes,emit=None):
  self.policy=policy;self.model=model;self.delay=delay;self.q=q;self.quotes=quotes;self.emit=emit or NullLog()
  self.cash=D(5000);self.inv=ZERO;self.fees=ZERO;self.maker_notional=ZERO;self.taker_notional=ZERO
  self.orders={};self.nextid=1;self.tasks=[];self.seq=0;self.count=Counter();self.unknown=[];self.risk_unknown=[]
  self.lasttime=0;self.exposure=ZERO;self.hold_since=None;self.longest_ticks=0;self.max_inventory_notional=ZERO;self.peak=D(5000);self.maxdd=ZERO
  self.m=None;self.attr_inventory=ZERO;self.attr_execution=ZERO;self.attr_fees=ZERO;self.attr_unknown=False
  self.terminal_done=False
 def log(self,t,event,o=None,**kw):
  self.emit.write(t,event,self,o,kw)
 def tick(self,t):
  if t<self.lasttime:raise ValueError('Engine time regression')
  self.exposure+=self.inv*D(t-self.lasttime)/T
  if self.inv>0 and self.hold_since is not None:self.longest_ticks=max(self.longest_ticks,t-self.hold_since)
  self.lasttime=t
 def reservations(self):
  cash=sum((o.price*o.leaves*(ONE+MAKER) for o in self.orders.values() if o.side=='buy'),ZERO)
  btc=sum((o.leaves for o in self.orders.values() if o.side=='sell'),ZERO)
  buy=sum((o.leaves for o in self.orders.values() if o.side=='buy'),ZERO)
  return cash,btc,buy
 def invariant(self):
  rc,ri,rb=self.reservations()
  if self.cash<0 or self.inv<0 or rc>self.cash or ri>self.inv or self.inv+rb>50*self.q:raise ArithmeticError('Cash/inventory/reserve invariant')
  if any(o.leaves<=0 or o.ahead<0 for o in self.orders.values()):raise ArithmeticError('Order quantity invariant')
 def reference(self,t,equal=False):return self.quotes.ref(t,equal)
 def observe(self,t,book=None):
  self.tick(t)
  if book is None:
   got=self.reference(t);book=got[1] if got else None
  if book is not None:
   m=(decimal_int(book[0])+decimal_int(book[2]))/2
   if self.m is not None:self.attr_inventory+=self.inv*(m-self.m)
   self.m=m
  elif self.inv:self.attr_unknown=True
  if self.inv==0:equity=self.cash;notional=ZERO
  elif book is None:
   self.risk_unknown.append((t,'reference_unavailable'));return
  else:
   try:g,f,_=liquidation(self.inv,book)
   except ValueError:
    self.risk_unknown.append((t,'depth_insufficient'));return
   equity=self.cash+g-f;notional=g/(ONE-SLIP)
  self.max_inventory_notional=max(self.max_inventory_notional,notional)
  self.peak=max(self.peak,equity);self.maxdd=max(self.maxdd,self.peak-equity)
 def schedule(self,t,kind,o):
  self.seq+=1;heapq.heappush(self.tasks,(t,0 if kind=='cancel' else 1,self.seq,kind,o.ident))
 def submit(self,t,side,price,maxsrc):
  if side in self.orders:return False
  rc,ri,rb=self.reservations()
  if side=='buy' and (price*self.q*(ONE+MAKER)>self.cash-rc or self.inv+rb+self.q>50*self.q):self.count['cash_or_buy_limit']+=1;return False
  if side=='sell' and self.inv-ri<self.q:self.count['insufficient_available_BTC']+=1;return False
  o=Order(self.nextid,side,price,self.q,self.q,t);o.maxsrc=maxsrc;self.nextid+=1;self.orders[side]=o
  self.schedule(t+self.delay,'accept',o);self.count['submitted']+=1;self.invariant();self.log(t,'submit',o);return True
 def cancel(self,t,o,reason):
  if o.cancel_at:return
  o.cancel_sent=t;o.cancel_at=max(t+self.delay,o.submit+self.delay)
  self.schedule(o.cancel_at,'cancel',o);self.count['cancel_sent']+=1;self.log(t,'cancel_sent',o,reason=reason)
 def decision(self,t,pause,maxsrc,safety=False):
  self.observe(t);got=self.reference(t)
  self.count['decision_grids']+=1
  if safety or not got:
   self.count['safety_pause']+=1
   for o in list(self.orders.values()):self.cancel(t,o,'common_safety')
   self.log(t,'grid',pause=pause,safety=True,reference_row=got[0] if got else None);return
  row,book=got
  self.log(t,'grid',pause=pause,safety=False,reference_row=row)
  for side,price in (('buy',decimal_int(book[2])),('sell',decimal_int(book[0]))):
   o=self.orders.get(side)
   if o is not None:
    if side==pause:self.cancel(t,o,'policy_pause')
    elif o.price!=price:self.cancel(t,o,'reprice_next_grid')
   elif side!=pause:self.submit(t,side,price,maxsrc)
  self.invariant()
 def process_tasks(self,t,maxsrc):
  self.observe(t)
  while self.tasks and self.tasks[0][0]<=t:
   tt,priority,seq,kind,oid=heapq.heappop(self.tasks)
   if tt!=t:raise ArithmeticError('Missed scheduled event')
   o=next((x for x in self.orders.values() if x.ident==oid),None)
   if o is None:continue
   if kind=='cancel':
    self.log(t,'cancel_effective',o);del self.orders[o.side];self.count['cancel_effective']+=1
   elif kind=='expiry':self.cancel(t,o,'TTL1s')
   else:
    got=self.reference(t)
    if not got:
     self.log(t,'reject_reference_missing',o);del self.orders[o.side];self.count['reject_reference_missing']+=1;continue
    row,book=got;ask=decimal_int(book[0]);bid=decimal_int(book[2])
    if (o.side=='buy' and o.price>=ask) or (o.side=='sell' and o.price<=bid):
     self.log(t,'reject_post_only',o);del self.orders[o.side];self.count['reject_post_only']+=1;continue
    offset=2 if o.side=='buy' else 0
    prices=[decimal_int(book[4*i+offset]) for i in range(25)]
    if not min(prices)<=o.price<=max(prices):
     self.unknown.append((t,'accepted_price_outside25',oid));self.log(t,'UNKNOWN_queue_outside25',o);del self.orders[o.side];continue
    o.ahead=sum((decimal_int(book[4*i+offset+1]) for i,p in enumerate(prices) if p==o.price),ZERO)
    o.state='active';o.accepted=t;o.maxsrc=maxsrc
    self.seq+=1;heapq.heappush(self.tasks,(t+T,0,self.seq,'expiry',o.ident))
    self.count['accepted']+=1;self.log(t,'accepted',o,reference_row=row)
  self.invariant()
 def fill(self,t,o,qty,price,kind,source=None,level=None,reference_book=None):
  if qty<=0 or qty>o.leaves:raise ArithmeticError('Invalid fill quantity')
  self.observe(t,reference_book)
  fee_rate=TAKER if kind=='terminal' else MAKER;notional=qty*price;fee=notional*fee_rate;dq=qty if o.side=='buy' else -qty
  before=self.inv
  self.cash-=dq*price+fee;self.inv+=dq;self.fees+=fee
  if kind=='terminal':self.taker_notional+=notional
  else:self.maker_notional+=notional
  if self.m is None:self.attr_unknown=True
  else:self.attr_execution+=dq*(self.m-price)
  self.attr_fees+=fee
  if before==0 and self.inv>0:self.hold_since=t
  if self.inv==0:self.hold_since=None
  o.leaves-=qty;self.count['fills']+=1;self.count[kind+'_fills']+=1
  self.log(t,'fill',o,qty=str(qty),fill_price=str(price),fee=str(fee),fee_rate=str(fee_rate),fill_kind=kind,trade_ids=source,depth_level=level)
  if kind!='terminal' and o.leaves==0:
   del self.orders[o.side];self.count['fully_filled_orders']+=1
  if kind!='terminal':self.invariant()
  self.observe(t,reference_book)
 def prints(self,t,trades):
  self.observe(t)
  for o in list(self.orders.values()):
   if o.state!='active' or t<=o.accepted:continue
   relevant=[x for x in trades if (x.typ==1 if o.side=='buy' else x.typ==0)]
   batches={}
   for tr in relevant:
    self.count['compatible_prints_seen']+=1
    near=abs(tr.src*10-o.accepted)<=10010 or (o.cancel_at and abs(tr.src*10-o.cancel_at)<=10010)
    if near:self.count['source_boundary_1ms_prints']+=1
    if not (tr.src*10>o.accepted and tr.src>o.maxsrc and (not o.cancel_at or tr.src*10<=o.cancel_at)):
     self.count['late_source_guard_prints']+=1;continue
    batches.setdefault(tr.price,[]).append(tr)
   # Same-capture/same-price compatible prints are aggregated. Price ordering is fixed,
   # not selected by future return; opposite price batches can affect only this one order.
   for price,group in sorted(batches.items(),reverse=o.side=='sell'):
    if o.side not in self.orders:break
    cross=self.model=='X' and ((o.side=='buy' and price<o.price) or (o.side=='sell' and price>o.price))
    if price!=o.price and not cross:continue
    v=sum((x.qty for x in group),ZERO);ahead0=o.ahead
    o.ahead,ex=consume(o.ahead,o.leaves,v,cross)
    if ex>v:raise ArithmeticError('Print double use')
    self.count['cross_print_batches' if cross else 'equal_print_batches']+=1
    if any(abs(x.src*10-o.accepted)<=10010 or (o.cancel_at and abs(x.src*10-o.cancel_at)<=10010) for x in group):
     self.count['boundary_batches_consumed']+=1
     if ex:self.count['boundary_batches_filled']+=1
    self.log(t,'queue_consume',o,print_qty=str(v),ahead_before=str(ahead0),executable=str(ex),cross=bool(cross),trade_ids=[x.ident for x in group])
    if ex:self.fill(t,o,ex,o.price,'cross' if cross else 'equal',[x.ident for x in group])
  self.invariant()
 def all_cancel(self,t):
  self.observe(t)
  for o in list(self.orders.values()):self.cancel(t,o,'terminal_all_cancel')
 def terminal(self,t,got):
  self.observe(t,got[1]);row,book=got
  if self.orders:raise ArithmeticError('Orders survive terminal cancellation')
  try:g,f,legs=liquidation(self.inv,book)
  except ValueError:
   self.unknown.append((t,'terminal_depth_insufficient'));self.log(t,'UNKNOWN_terminal_depth',reference_row=row);return
  if self.inv:
   o=Order(self.nextid,'sell',ZERO,self.inv,self.inv,t,state='active',accepted=t)
   for level,px,q,fee in legs:self.fill(t,o,q,px,'terminal',level=level,reference_book=book)
  self.terminal_done=True;self.invariant();self.log(t,'terminal_complete',reference_row=row)
 def result(self):
  unknown=bool(self.unknown or self.risk_unknown or not self.terminal_done)
  pnl=self.cash-D(5000) if self.terminal_done else None
  attr=None if self.attr_unknown or pnl is None else {'inventory_price':str(self.attr_inventory),'execution_price':str(self.attr_execution),'fees':str(self.attr_fees),'identity_residual':str(pnl-(self.attr_inventory+self.attr_execution-self.attr_fees))}
  return {'policy':self.policy,'model':self.model,'delay_ms':self.delay//10000,'status':'UNKNOWN' if unknown else 'MODEL_PATH_COMPLETE','cash':str(self.cash),'BTC':str(self.inv),'PnL_USD':str(pnl) if pnl is not None else None,'fees_USD':str(self.fees),'maker_notional':str(self.maker_notional),'taker_notional':str(self.taker_notional),'inventory_BTC_seconds':str(self.exposure),'max_inventory_notional_USD':str(self.max_inventory_notional),'max_drawdown_USD':str(self.maxdd),'longest_positive_inventory_seconds':str(D(self.longest_ticks)/T),'unknown':self.unknown,'risk_unknown_count':len(self.risk_unknown),'first_risk_unknown':self.risk_unknown[:3],'counts':dict(self.count),'attribution':attr,'attribution_status':'UNKNOWN' if attr is None else 'ACCOUNTING_ONLY_NOT_CAUSAL_ALPHA','q_BTC':str(self.q)}

def policy_pause(day,sec,sign):
 if not sign:return None,None
 f='sell' if sign>0 else 'buy'
 key=f'XTX-adverse-proxy-v1|{day}T{sec//3600:02d}:{sec%3600//60:02d}:{sec%60:02d}Z'
 h='buy' if hashlib.sha256(key.encode()).digest()[0]<128 else 'sell'
 return f,h
