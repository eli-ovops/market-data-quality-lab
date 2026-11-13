"""Necessary artificial lifecycle/accounting checks; no historical input."""
from core import *
from inputs import Quotes,integer_value
class Log:
 def __init__(self):self.rows=[]
 def write(self,t,event,e,o,detail):self.rows.append((t,event,detail))
def quotes(cap=0,amount='10'):
 q=Quotes();book=[]
 for i in range(25):book.extend((integer_value(str(101+i),True),integer_value(amount),integer_value(str(100-i),True),integer_value(amount)))
 
 for j in range(21):
  c=cap+j*T//2;q.cap.append(c);q.src.append(c//10);q.row.append(j+1);q.bad.append(0);q.values.extend(book)
 return q
def engine(delay=T//10):return Engine('F','E',delay,D('1'),quotes(),Log())
def buy(e,t,q):
 o=Order(900+e.lotseq,'buy',D(100),D(q),D(q),t,state='active');e.orders['buy']=o;e.fill(t,o,D(q),D(100),'equal')
def sell(e,t,q):
 o=Order(990,'sell',D(101),D(q),D(q),t,state='active');e.orders['sell']=o;e.fill(t,o,D(q),D(101),'equal')
def run():
 out=[]
 def check(n,fn):
  fn();out.append({'name':n,'pass':True})
 def assert_(v):
  if not v:raise AssertionError('Synthetic expected assertion failed')
 check('unchanged maker equal/cross consumption',lambda:assert_(consume(D(2),D(3),D(4))==(ZERO,D(2)) and consume(D(9),D(3),D(2),True)==(ZERO,D(2))))
 e=engine();buy(e,1,D('.4'));buy(e,2,D('.6'));sell(e,3,D('.5'))
 check('FIFO partial maker sale',lambda:assert_(e.lots[0]['remaining']==0 and e.lots[1]['remaining']==D('.5') and e.inv==D('.5')))
 check('exact accounting after partial FIFO',lambda:e.invariant())
 e=engine();buy(e,1,D('.4'));d=T+1;e.begin_due(d)
 check('one-second trigger/barrier',lambda:assert_(e.phase=='barrier' and e.send_at==d+e.delay))
 check('locked submit leaves fixed q unchanged',lambda:assert_(not e.submit(d,'buy',D(100),-1) and e.q==1))
 e.age_step(e.send_at);u=e.arrive_at
 check('second delay and frozen quantity',lambda:assert_(u==d+2*e.delay and e.exit_qty==D('.4') and e.inv==D('.4')))
 check('exit reservation is BTC subset',lambda:assert_(e.reservations()[1]==D('.4')))
 e.age_step(u)
 check('sub-q exit complete FIFO',lambda:assert_(e.inv==0 and e.exit_qty==0 and e.age_fees==D('.4')*D('99.99')*TAKER))
 check('strictly next grid no same-time restart',lambda:assert_(not e.submit(u,'buy',D(100),-1)))
 check('lot and cash conservation after age exit',lambda:e.invariant())
 e=engine(T//2);buy(e,1,D('.4'));buy(e,T//4,D('.6'));e.begin_due(T+1);e.age_step(e.send_at)
 check('later-matured before send joins fixed allocation',lambda:assert_(e.exit_qty==1 and len(e.exit_alloc)==2))
 frozen=list(e.exit_alloc);qty=e.exit_qty
 check('send allocation immutable until arrival',lambda:assert_(e.exit_alloc==frozen and e.exit_qty==qty))
 e.age_step(e.arrive_at)
 check('500ms two-stage completes at two seconds',lambda:assert_(e.lasttime==2*T+1 and e.inv==0))
 e=engine();buy(e,1,D('.4'));buy(e,T//2,D('.6'));e.begin_due(T+1);e.age_step(e.send_at)
 check('not-yet-due lot excluded from sent quantity',lambda:assert_(e.exit_qty==D('.4') and len(e.exit_alloc)==1))
 e.age_step(e.arrive_at)
 check('unmatured lot retains timer',lambda:assert_(e.inv==D('.6') and e.next_age_event()==T+T//2))
 e=engine();buy(e,1,D('.4'));e.begin_due(T+1);sell(e,T+2,D('.4'));tau=e.send_at;e.age_step(tau)
 check('Q0 no nonexistent arrival/fee',lambda:assert_(e.phase=='idle' and e.exit_qty==0 and e.age_fees==0 and e.resume_after==tau))
 check('Q0 same-time submit blocked',lambda:assert_(not e.submit(tau,'buy',D(100),-1)))
 e=engine();buy(e,1,D('.4'));e.begin_due(T+1);e.age_step(e.send_at);
 for i in range(len(e.quotes.bad)):e.quotes.bad[i]=1
 e.age_step(e.arrive_at)
 check('missing reference freezes with inventory/exit preserved',lambda:assert_(e.frozen and e.inv==D('.4') and e.exit_qty==D('.4') and not e.terminal_done))
 e=engine();e.quotes=quotes(amount='.01');buy(e,1,D('1'));e.begin_due(T+1);e.age_step(e.send_at);cash=e.cash;e.age_step(e.arrive_at)
 check('insufficient full depth no partial execution',lambda:assert_(e.frozen and e.cash==cash and e.inv==1))
 e=engine();buy(e,1,D('1'));got=e.reference(2);e.execute_exit(2,got,D('.4'),'terminal');before=e.depth_left[0];e.execute_exit(3,got,D('.6'),'terminal')
 check('same group finite cumulative budget',lambda:assert_(e.depth_left[0]==before-D('.6') and e.depth_left[0]==9))
 check('same group reset logged only once',lambda:assert_(sum(x[1]=='exit_depth_reset' for x in e.emit.rows)==1))
 e=engine();buy(e,1,D('1'));e.execute_exit(2,e.reference(2),D('.4'),'terminal');e.observe(3)
 check('consumed fullbook nonzero inventory risk UNKNOWN',lambda:assert_(any(x[1]=='exit_consumed_reference_fullbook_unavailable' for x in e.risk_unknown)))
 e=engine();buy(e,1,D('.4'));e.begin_due(T+1);e.age_step(e.send_at);e.takeover(e.send_at+1)
 check('terminal takeover preserves sent exit',lambda:assert_(e.phase=='flight' and e.exit_qty==D('.4')))
 e.age_step(e.arrive_at);e.terminal(e.arrive_at+1,e.reference(e.arrive_at+1))
 check('sent exit then terminal no double sell',lambda:assert_(e.inv==0 and e.sell_quantity==D('.4') and e.terminal_done))
 e=engine();buy(e,1,D('.4'));e.begin_due(T+1);e.takeover(T+2)
 check('unsent barrier takeover leaves lots',lambda:assert_(e.phase=='idle' and e.inv==D('.4') and e.terminal_mode))
 e=engine();buy(e,1,D('1'));e.submit(2,'sell',D(101),-1);e.process_tasks(2+e.delay,-1);e.begin_due(T+1)
 while e.tasks and e.tasks[0][0]<=e.send_at:
  t=e.tasks[0][0];e.process_tasks(t,-1)
 e.age_step(e.send_at)
 check('pending conflict cancelled before exit reserve',lambda:assert_(not e.orders and e.exit_qty==1))
 e=engine();e.original_sign=1;e.phase='barrier';e.decision(1,'sell',-1)
 check('locked grid/score still logged',lambda:assert_(e.count['decision_grids']==1 and any(x[1]=='grid' and x[2]['original_sign']==1 for x in e.emit.rows)))
 e=engine();buy(e,1,D('.4'));e.begin_due(T+1);e.age_step(e.send_at);e.age_step(e.arrive_at)
 check('fill evidence includes FIFO updates',lambda:assert_(all('fifo_allocation' in x[2] and 'lot_remaining_total' in x[2] for x in e.emit.rows if x[1]=='fill')))
 return out
