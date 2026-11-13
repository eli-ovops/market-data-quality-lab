"""Only artificial fixtures. No actual source/imported old experiment or market reads."""
from core import *
from inputs import Quotes,integer_value,score_at,cap
import array
class Recorder:
 def __init__(self):self.rows=[]
 def write(self,t,event,e,o,kw):self.rows.append((t,event,kw,str(e.cash),str(e.inv)))
class Fixture:
 def __init__(self,bid='99',ask='101',qty='10'):self.book0=[];self.available=True
 def configure(self,bid='99',ask='101',qty='10'):
  self.book0=[]
  for i in range(25):self.book0.extend([integer_value(str(D(ask)+i)),integer_value(qty),integer_value(str(D(bid)-i)),integer_value(qty)])
  return self
 def ref(self,t,equal=False):return (1,self.book0) if self.available else None

def run():
 out=[]
 def check(name,fn):
  fn();out.append({'name':name,'pass':True})
 def eq(a,b):assert a==b,(a,b)
 check('q downward12places',lambda:eq(quantity(D(3)),D('16.666666666666')))
 check('sameprint ahead and fill share qty',lambda:eq(consume(D(3),D(5),D(4)),(ZERO,D(1))))
 check('sameprint no fill before ahead',lambda:eq(consume(D(10),D(5),D(3)),(D(7),ZERO)))
 check('cross ignores old ahead bounded by print',lambda:eq(consume(D(99),D(5),D(2),True),(ZERO,D(2))))
 check('cross bounded by leaves',lambda:eq(consume(D(99),D(1),D(3),True),(ZERO,D(1))))
 check('100ns exact timestamp',lambda:eq(cap('2026-05-01T00:00:00.1234567Z')%T,1234567))
 check('fixedpoint raw precision',lambda:eq(integer_value('0.00000001'),10000))
 check('cash-only stale risk remains known',lambda:cash_only())
 def quotes():
  f=Fixture().configure();q=Quotes()
  for t,bad in ((10,False),(20,True),(30,False)):
   q.cap.append(t);q.src.append(0);q.row.append(t);q.bad.append(bad);q.values.extend(f.book0)
  return q
 def refs():
  q=quotes();eq(q.ref(20)[0],10);eq(q.ref(21),None);eq(q.ref(31)[0],30);eq(q.ref(T+31),None)
 check('strict latest invalid never fallback and age',refs)
 def terminal():
  q=quotes();eq(q.terminal(21,29),None);eq(q.terminal(21,31)[0],30)
 check('terminal first valid arriving no price selection',terminal)
 def reserve():
  f=Fixture().configure();e=Engine('F','E',10,D(1),f);eq(e.submit(100,'sell',D(101),0),False)
  eq(e.submit(100,'buy',D(99),0),True);eq(e.reservations()[0],D('99.297'));e.invariant()
 check('BTC0 no naked sell and buy fee reserve',reserve)
 def lifecycle():
  f=Fixture().configure(qty='1');r=Recorder();e=Engine('F','E',10,D(1),f,r)
  e.submit(100,'buy',D(99),0);e.process_tasks(110,-1);o=e.orders['buy'];eq(o.ahead,D(1));e.cancel(120,o,'test')
  # Same-capture print before cancel at130 still fills. source us*10<=cancel.
  e.prints(130,[Trade(130,12,1,1,D(99),D('1.5'))]);eq(e.inv,D('.5'));eq(e.orders['buy'].leaves,D('.5'))
  e.process_tasks(130,12);eq(e.orders,{});eq(e.reservations(),(ZERO,ZERO,ZERO));eq(e.cash,D('4950.3515'))
 check('cancel race partialfill preserved cash and reserve released only effect',lifecycle)
 def late():
  f=Fixture().configure(qty='0');e=Engine('F','X',10,D(1),f);e.submit(100,'buy',D(99),0);e.process_tasks(110,11)
  e.prints(120,[Trade(120,10,1,1,D(98),D(1))]);eq(e.inv,ZERO)
  e.prints(130,[Trade(130,12,2,1,D(98),D('.2'))]);eq(e.inv,D('.2'));eq(e.orders['buy'].ahead,ZERO)
 check('late-source rejection then crossing at ownlimit partial',late)
 def equal_vs_cross():
  for model,expect in (('E',ZERO),('X',D('.2'))):
   f=Fixture().configure(qty='10');e=Engine('F',model,10,D(1),f);e.submit(100,'buy',D(99),0);e.process_tasks(110,-1)
   e.prints(130,[Trade(130,12,1,1,D(98),D('.2'))]);eq(e.inv,expect)
 check('E ignores strictcross X caps printqty not fullorder',equal_vs_cross)
 def opposing():
  f=Fixture().configure(qty='0');e=Engine('F','X',10,D(1),f);e.submit(100,'buy',D(99),0);e.process_tasks(110,-1)
  e.prints(130,[Trade(130,12,1,0,D(98),D(1))]);eq(e.inv,ZERO)
 check('incompatible aggressor does not fill',opposing)
 def samecapture():
  f=Fixture().configure(qty='0');e=Engine('F','X',10,D(1),f);e.submit(100,'buy',D(99),0)
  e.prints(110,[Trade(110,11,1,1,D(98),D(1))]);e.process_tasks(110,-1);eq(e.inv,ZERO)
 check('print before acceptance same clock cannot fill neworder',samecapture)
 def postonly():
  f=Fixture().configure();e=Engine('F','E',10,D(1),f);e.submit(100,'buy',D(102),0);e.process_tasks(110,-1);eq(e.orders,{});eq(e.inv,ZERO)
 check('GTX crossed at accept rejects no taker',postonly)
 def ttl():
  f=Fixture().configure();e=Engine('F','E',10,D(1),f);e.submit(100,'buy',D(99),0);e.process_tasks(110,-1)
  e.process_tasks(110+T,-1);eq(e.orders['buy'].cancel_at,120+T);eq(e.reservations()[0],D('99.297'));e.process_tasks(120+T,-1);eq(e.orders,{})
 check('TTL1s sends cancel plus delay not immediate deletion',ttl)
 def stale():
  f=Fixture().configure();e=Engine('F','E',10,D(1),f);e.submit(100,'buy',D(99),0);e.process_tasks(110,-1);f.available=False
  e.decision(120,None,0);eq(e.orders['buy'].cancel_at,130);eq(e.reservations()[0],D('99.297'));e.process_tasks(130,-1);eq(e.cash,D(5000))
 check('stale safety keeps in-flight order reserve until cancel',stale)
 def pnl():
  f=Fixture().configure(bid='100',ask='102',qty='2');r=Recorder();e=Engine('F','X',10,D(1),f,r)
  e.submit(100,'buy',D(99),0);e.process_tasks(110,-1);e.prints(130,[Trade(130,12,1,1,D(98),D(1))])
  # q fully fills at own99, fee .297; terminal100*.9999 less .4%.
  e.terminal(200,(1,f.book0));eq(e.inv,ZERO);eq(e.cash,D('5000.29304'));eq(e.fees,D('.69696'))
  a=e.result()['attribution'];eq(D(a['identity_residual']),ZERO)
 check('ownlimit maker plus terminaltaker slip exactcash attribution',pnl)
 def ladder():
  f=Fixture().configure(bid='100',ask='102',qty='1');g,fee,legs=liquidation(D('1.5'),f.book0)
  eq(len(legs),2);eq(g,D('149.48505'));eq(fee,D('.59794020'));eq(sum((x[2] for x in legs),ZERO),D('1.5'))
 check('terminal sweeps levels no repeated volume fees',ladder)
 def depthfail():
  f=Fixture().configure(qty='0');e=Engine('F','E',10,D(1),f);e.inv=D(1);e.terminal(200,(1,f.book0));eq(e.inv,D(1));eq(e.terminal_done,False);eq(e.result()['status'],'UNKNOWN')
 check('insufficient terminal depth retains inventory UNKNOWN',depthfail)
 def pendingreject():
  f=Fixture().configure();e=Engine('F','E',10,D(1),f);e.submit(100,'buy',D(99),0);f.available=False;e.process_tasks(110,-1);eq(e.cash,D(5000));eq(e.orders,{})
 check('accept reference stale rejected pending released at effect',pendingreject)
 def caprisk():
  f=Fixture().configure();e=Engine('F','E',10,D(1),f);e.inv=D(50);eq(e.submit(100,'buy',D(99),0),False)
 check('50q includes pendingbuys bound',caprisk)
 def boundary():
  ts=[Trade(10*T,1,1,0,D(1),D(1))];eq(score_at(10*T,ts,[10*T])[1],True)
 check('signal original100ns membership boundary unknown',boundary)
 def hashcheck():
  f,h=policy_pause('2026-05-01',5,1);eq(f,'sell');eq(h in ('buy','sell'),True);eq(policy_pause('2026-05-01',5,0),(None,None))
 check('same common nonzero grids fixedhash',hashcheck)
 return out

def cash_only():
 f=Fixture().configure();f.available=False;e=Engine('F','E',10,D(1),f);e.observe(123);assert not e.risk_unknown;assert e.maxdd==0
