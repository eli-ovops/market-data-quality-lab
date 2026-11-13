"""Inventory-age extension of byte-preserved maker engine; no external execution."""
from base_core import *
import bisect

BaseEngine=Engine
INF=2**63-1
class Engine(BaseEngine):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw)
  self.lots=[];self.lotseq=0;self.phase='idle';self.trigger=0;self.send_at=0;self.arrive_at=0
  self.exit_qty=ZERO;self.exit_alloc=[];self.resume_after=-1;self.terminal_mode=False;self.frozen=False
  self.depth_cap=-1;self.depth_row=None;self.depth_left=[];self.depth_consumed=False
  self.age_notional=ZERO;self.age_fees=ZERO;self.terminal_notional=ZERO;self.terminal_fees=ZERO
  self.lock_start=None;self.lock_ticks=0;self.original_sign=0;self.max_BTC=ZERO;self.txseq=0
 def log(self,t,event,o=None,**kw):
  if event.startswith(('age_','exit_')):kw.update(transaction_id=self.txseq,exit_reserved=str(self.exit_qty))
  if event=='grid':kw.update(original_sign=self.original_sign,inventory_exit_phase=self.phase,resume_after=self.resume_after)
  super().log(t,event,o,**kw)
 def reservations(self):
  c,b,rb=super().reservations();return c,b+self.exit_qty,rb
 def invariant(self):
  super().invariant()
  if sum((x['remaining'] for x in self.lots),ZERO)!=self.inv:raise ArithmeticError('FIFO quantity residual')
  if any(x['remaining']<0 for x in self.lots):raise ArithmeticError('Negative FIFO lot')
  if self.exit_qty<0 or self.exit_qty>self.inv:raise ArithmeticError('Exit reservation residual')
  if self.exit_qty!=sum((q for i,q in self.exit_alloc),ZERO):raise ArithmeticError('Exit allocation residual')
 def fifo_sell(self,q):
  alloc=[];rem=q
  for lot in self.lots:
   take=min(rem,lot['remaining'])
   if take:lot['remaining']-=take;rem-=take;alloc.append((lot['id'],str(take)))
   if not rem:break
  if rem:raise ArithmeticError('FIFO oversell')
  return alloc
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
  elif book is None:self.risk_unknown.append((t,'reference_unavailable'));return
  else:
   got=self.reference(t)
   if got and self.depth_consumed and self.book_cap(got[0])==self.depth_cap:
    self.risk_unknown.append((t,'exit_consumed_reference_fullbook_unavailable'));return
   try:g,f,_=liquidation(self.inv,book)
   except ValueError:self.risk_unknown.append((t,'depth_insufficient'));return
   equity=self.cash+g-f;notional=g/(ONE-SLIP)
  self.max_inventory_notional=max(self.max_inventory_notional,notional)
  self.peak=max(self.peak,equity);self.maxdd=max(self.maxdd,self.peak-equity)
 def book_cap(self,row):
  j=bisect.bisect_left(self.quotes.row,row)
  if j>=len(self.quotes.row) or self.quotes.row[j]!=row:raise ArithmeticError('Unknown snapshot group row')
  return self.quotes.cap[j]
 def submit(self,t,side,price,maxsrc):
  if self.phase!='idle' or t<=self.resume_after or self.terminal_mode:
   self.count['inventory_exit_submission_blocked']+=1;self.log(t,'inventory_exit_submission_blocked',side=side);return False
  return super().submit(t,side,price,maxsrc)
 def decision(self,t,pause,maxsrc,safety=False):
  if not self.frozen:return super().decision(t,pause,maxsrc,safety)
 def prints(self,t,trades):
  if not self.frozen:return super().prints(t,trades)
 def process_tasks(self,t,maxsrc):
  if self.frozen:return
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
    if bid<o.price<ask:o.ahead=ZERO;self.count['inside_spread_accepted']+=1
    else:
     prices=[decimal_int(book[4*i+offset]) for i in range(25)]
     if not min(prices)<=o.price<=max(prices):
      # Unlike the prior unit: first execution UNKNOWN preserves its unresolved
      # order and reservations, and freezes this path immediately.
      self.unknown.append((t,'accepted_price_outside25',oid));self.frozen=True
      self.log(t,'UNKNOWN_path_frozen',o,reason='accepted_price_outside25',reference_row=row)
      self.invariant();return
     o.ahead=sum((decimal_int(book[4*i+offset+1]) for i,p in enumerate(prices) if p==o.price),ZERO)
    o.state='active';o.accepted=t;o.maxsrc=maxsrc
    self.seq+=1;heapq.heappush(self.tasks,(t+T,0,self.seq,'expiry',o.ident))
    self.count['accepted']+=1;self.log(t,'accepted',o,reference_row=row)
  self.invariant()
 def fill(self,t,o,qty,price,kind,source=None,level=None,reference_book=None,risk_observe=True):
  if qty<=0 or qty>o.leaves:raise ArithmeticError('Invalid fill quantity')
  if risk_observe:self.observe(t,reference_book)
  else:self.tick(t)
  rate=TAKER if kind in ('terminal','age_exit') else MAKER;notional=qty*price;fee=notional*rate;dq=qty if o.side=='buy' else -qty;before=self.inv
  if o.side=='buy':
   self.buy_quantity+=qty;self.buy_notional+=notional;self.lotseq+=1
   lot={'id':self.lotseq,'buy_t':t,'due':t+T,'initial':qty,'remaining':qty};self.lots.append(lot);allocation=[(lot['id'],str(qty))]
  else:
   self.sell_quantity+=qty;self.sell_notional+=notional;allocation=self.fifo_sell(qty)
  self.cash-=dq*price+fee;self.inv+=dq;self.max_BTC=max(self.max_BTC,self.inv);self.fees+=fee
  if kind in ('terminal','age_exit'):self.taker_notional+=notional
  else:self.maker_notional+=notional
  if kind=='age_exit':self.age_notional+=notional;self.age_fees+=fee
  if kind=='terminal':self.terminal_notional+=notional;self.terminal_fees+=fee
  if self.m is None:self.attr_unknown=True
  else:self.attr_execution+=dq*(self.m-price)
  self.attr_fees+=fee
  if before==0 and self.inv>0:self.hold_since=t
  if self.inv==0:self.hold_since=None
  o.leaves-=qty;self.count['fills']+=1;self.count[kind+'_fills']+=1
  self.log(t,'fill',o,qty=str(qty),fill_price=str(price),fee=str(fee),fee_rate=str(rate),fill_kind=kind,trade_ids=source,depth_level=level,fifo_allocation=allocation,lot_remaining_total=str(sum((x['remaining'] for x in self.lots),ZERO)),lot_updates=[{'id':i,'remaining':str(next(x['remaining'] for x in self.lots if x['id']==i))} for i,_ in allocation],buy_lot_due=t+T if o.side=='buy' else None)
  if kind not in ('terminal','age_exit') and o.leaves==0:del self.orders[o.side];self.count['fully_filled_orders']+=1
  if kind not in ('terminal','age_exit'):self.invariant()
  if risk_observe:self.observe(t,reference_book)
 def next_age_event(self):
  if self.frozen:return INF
  if self.phase=='flight':return self.arrive_at
  if self.terminal_mode:return INF
  if self.phase=='barrier':return self.send_at
  return min((x['due'] for x in self.lots if x['remaining']),default=INF)
 def begin_due(self,t):
  if self.frozen or self.terminal_mode or self.phase!='idle':return
  if not any(x['remaining'] and x['due']<=t for x in self.lots):return
  self.observe(t);self.phase='barrier';self.trigger=t;self.send_at=t+self.delay;self.lock_start=t
  self.count['age_transactions']+=1;self.txseq+=1
  for o in list(self.orders.values()):self.cancel(t,o,'inventory_age_exit')
  self.log(t,'age_trigger',send_at=self.send_at)
 def release_lock(self,t):
  if self.lock_start is not None:self.lock_ticks+=t-self.lock_start
  self.lock_start=None;self.phase='idle';self.resume_after=t
 def freeze(self,t,reason,**detail):
  self.observe(t);self.unknown.append((t,reason));self.frozen=True;self.log(t,'UNKNOWN_path_frozen',reason=reason,**detail)
 def plan_depth(self,got,q):
  row,book=got;cap=self.book_cap(row)
  if cap<self.depth_cap:raise ArithmeticError('Exit depth snapshot regression')
  left=[decimal_int(book[4*i+3]) for i in range(25)] if cap>self.depth_cap else list(self.depth_left)
  if not left and q:raise ArithmeticError('Uninitialized exit depth')
  rem=q;legs=[]
  for i in range(25):
   take=min(rem,left[i])
   if take:
    before=left[i];left[i]-=take;rem-=take
    legs.append((i,decimal_int(book[4*i+2])*(ONE-SLIP),take,before,left[i]))
   if not rem:break
  if rem:return None
  return cap,row,left,legs
 def execute_exit(self,t,got,q,kind):
  plan=self.plan_depth(got,q)
  if plan is None:self.freeze(t,kind+'_depth_budget_insufficient',quantity=str(q),reference_row=got[0]);return False
  cap,row,left,legs=plan
  is_new=cap>self.depth_cap
  if is_new:self.log(t,'exit_depth_reset',reference_capture=cap,reference_row=row,amounts=[str(decimal_int(got[1][4*i+3])) for i in range(25)])
  self.observe(t,got[1])
  # Reservation/allocation are released exactly as this one atomic sell executes.
  if kind=='age_exit':
   expected=[(i,str(qty)) for i,qty in self.exit_alloc]
   actual=[];remaining=q
   for lot in self.lots:
    take=min(remaining,lot['remaining'])
    if take:actual.append((lot['id'],str(take)));remaining-=take
    if not remaining:break
   if actual!=expected:raise ArithmeticError('Frozen FIFO exit allocation changed')
   self.exit_qty=ZERO;self.exit_alloc=[]
  o=Order(self.nextid,'sell',ZERO,q,q,t,state='active',accepted=t);self.nextid+=1
  for i,px,v,before,after in legs:
   self.fill(t,o,v,px,kind,level=i,reference_book=got[1],risk_observe=False)
   self.log(t,'exit_depth_use',o,kind=kind,reference_row=row,reference_capture=cap,level=i,before=str(before),used=str(v),after=str(after))
  self.depth_cap=cap;self.depth_row=row;self.depth_left=left;self.depth_consumed=bool(legs) if is_new else self.depth_consumed or bool(legs)
  self.invariant();self.observe(t,got[1]);return True
 def age_step(self,t):
  if self.frozen:return
  if self.phase=='flight' and t==self.arrive_at:
   got=self.reference(t)
   if not got:self.freeze(t,'age_exit_reference_missing',quantity=str(self.exit_qty));return
   q=self.exit_qty
   if not self.execute_exit(t,got,q,'age_exit'):return
   self.count['age_exits_complete']+=1;self.log(t,'age_exit_complete',quantity=str(q));self.release_lock(t)
   self.begin_due(t)
  if self.phase=='barrier' and t==self.send_at:
   if self.terminal_mode:return
   if self.orders or any(self.reservations()):raise ArithmeticError('Age cancel barrier not closed')
   alloc=[(x['id'],x['remaining']) for x in self.lots if x['remaining'] and x['due']<=t]
   q=sum((v for _,v in alloc),ZERO)
   if not q:self.count['age_Q0']+=1;self.log(t,'age_Q0');self.release_lock(t);return
   self.exit_qty=q;self.exit_alloc=alloc;self.phase='flight';self.arrive_at=t+self.delay
   self.invariant();self.log(t,'age_exit_sent',quantity=str(q),allocation=[(i,str(v)) for i,v in alloc],arrive_at=self.arrive_at)
 def takeover(self,t):
  self.terminal_mode=True
  if self.phase=='barrier':self.log(t,'age_unsent_terminal_takeover');self.release_lock(t)
  self.all_cancel(t)
 def terminal(self,t,got):
  if self.orders or self.exit_qty or self.phase=='flight':raise ArithmeticError('Outstanding reservations at terminal')
  if not self.execute_exit(t,got,self.inv,'terminal'):return
  self.terminal_done=True;self.log(t,'terminal_complete',reference_row=got[0]);self.invariant()
 def result(self):
  r=super().result();r.update(policy=self.policy+'1',age_exit_notional=str(self.age_notional),age_exit_fees=str(self.age_fees),terminal_notional=str(self.terminal_notional),terminal_fees=str(self.terminal_fees),exit_reserved_BTC=str(self.exit_qty),lot_remaining_BTC=str(sum((x['remaining'] for x in self.lots),ZERO)),lot_count=len(self.lots),age_phase=self.phase,frozen=self.frozen,inventory_exit_lock_seconds=str(D(self.lock_ticks)/T),max_BTC=str(self.max_BTC),remaining_lots=[{k:str(v) if isinstance(v,D) else v for k,v in x.items()} for x in self.lots if x['remaining']])
  return r
