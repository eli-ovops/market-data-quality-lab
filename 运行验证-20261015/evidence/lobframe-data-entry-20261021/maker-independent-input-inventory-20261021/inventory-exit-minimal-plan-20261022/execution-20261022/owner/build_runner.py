from pathlib import Path
p=Path(__file__).parent/'run.py';s=p.read_text()
s=s.replace('UNIT=OUT.parent.parent','UNIT=OUT.parents[2]')
s=s.replace('2026,10,22,13,8,23','2026,10,22,16,1,37').replace("SOURCES=('core.py','inputs.py','run.py','tests.py','spec.json')","SOURCES=('base_core.py','core.py','inputs.py','run.py','tests.py','base_tests.py','spec.json')")
s=s.replace('rem=390-self.prior','rem=450-self.prior').replace('>=390','>=450').replace('CPU390','CPU450').replace('67108864','125829120').replace("'conservative_old_CPU_debit_seconds':150,'review_reserve_CPU_seconds':60","'conservative_old_CPU_debit_seconds':0,'review_reserve_CPU_seconds':150").replace('150+r[\'cumulative_Owner_CPU_seconds\']+60',"r['cumulative_Owner_CPU_seconds']+150")
s=s.replace("'conservative_old_CPU_debit_seconds':150", "'conservative_old_CPU_debit_seconds':0")
s=s.replace("'review_reserve_CPU_seconds':60", "'review_reserve_CPU_seconds':150")
s=s.replace("f=next(r for r in allresults if r['day']==day and r['policy']=='F'", "f=next(r for r in allresults if r['day']==day and r['policy']=='F1'").replace("h=next(r for r in allresults if r['day']==day and r['policy']=='H'", "h=next(r for r in allresults if r['day']==day and r['policy']=='H1'")
s=s.replace("comparisons.append(compare_paths(day,model,ms,f,h))", "c=compare_paths(day,model,ms,f,h)\n    old=json.loads((UNIT/'economic-correction-20261022'/'owner'/'result.json').read_text())\n    if sha(UNIT/'economic-correction-20261022'/'owner'/'result.json')!=json.loads((OUT.parent/'root'/'authorization.json').read_text())['old_owner_result_sha256']:raise ValueError('Old baseline identity')\n    oc=next(x for x in old['comparisons'] if x['day']==day and x['model']==model and x['delay_ms']==ms)\n    c.update(F0_PnL_USD=oc['F_PnL_USD'],H0_PnL_USD=oc['H_PnL_USD'],old_delta_F_minus_H_USD=oc['delta_F_minus_H_USD'],F1_minus_F0_USD=str(D(f['PnL_USD'])-D(oc['F_PnL_USD'])) if c['F_cash_complete'] else None,H1_minus_H0_USD=str(D(h['PnL_USD'])-D(oc['H_PnL_USD'])) if c['H_cash_complete'] else None,old_new_matched_price_risk='UNKNOWN')\n    comparisons.append(c)")
a=s.index('def simulate_day(');b=s.index('\ndef main():',a)
s=s[:a]+'''def simulate_day(day,start,trades,quotes,budget,allresults):
 firstj=next((j for j in range(len(quotes.cap)) if quotes.cap[j]<start+5*T and quotes.src[j]*10<quotes.cap[j] and not quotes.bad[j]),None)
 if firstj is None:raise ValueError('No initial BBO; no shift')
 p0=(decimal_int(quotes.book(firstj)[0])+decimal_int(quotes.book(firstj)[2]))/2;q=quantity(p0)
 expected={'2026-05-01':D('.000655226413'),'2026-06-01':D('.000679560327')}
 if q!=expected[day]:raise ValueError('Frozen q changed')
 ledger=Ledger(OUT/(day+'-ledger.csv.gz'))
 es=[Engine(p,m,d,q,quotes,ledger) for m in ('E','X') for d in (T//10,T//2) for p in ('F','H')]
 caps=[x.cap for x in trades];prefix=[];mx=-1
 for tr in trades:mx=max(mx,tr.src);prefix.append(mx)
 def maxsrc(t):
  j=bisect.bisect_left(caps,t);return prefix[j-1] if j else -1
 ti=bisect.bisect_left(caps,start+5*T);grid=5;cancelled=False;terminal=quotes.terminal(start+32451*T,start+32452*T)
 if terminal is None:raise ValueError('No fixed terminal reference')
 termtime,termref=terminal;done=False;steps=0
 try:
  for e in es:e.log(start+5*T,'initial',p0=str(p0),q=str(q),unit_assumption='BTC')
  while not done:
   live=[e for e in es if not e.frozen]
   ttrade=caps[ti] if ti<len(caps) else 2**63-1
   tgrid=start+grid*T if grid<=32449 else 2**63-1
   ttask=min((e.tasks[0][0] for e in live if e.tasks),default=2**63-1)
   tage=min((e.next_age_event() for e in live),default=2**63-1)
   tcancel=start+32450*T if not cancelled else 2**63-1
   t=min(ttrade,tgrid,ttask,tage,tcancel,termtime)
   if t>termtime:raise ArithmeticError('Timeline surpassed terminal')
   if t==ttrade:
    batch=[]
    while ti<len(caps) and caps[ti]==t:batch.append(trades[ti]);ti+=1
    for e in live:e.prints(t,batch)
   for e in live:
    if t<start+32450*T:e.begin_due(t)
   deferred={}
   for e in live:
    due=[]
    while e.tasks and e.tasks[0][0]==t:due.append(heapq.heappop(e.tasks))
    deferred[id(e)]=[x for x in due if x[3]=='accept']
    for x in due:
     if x[3]!='accept':heapq.heappush(e.tasks,x)
    if e.tasks and e.tasks[0][0]==t:e.process_tasks(t,maxsrc(t))
   # At terminal takeover: process already-sent arrivals, but never send new exits.
   for e in live:
    if t>=start+32450*T:e.terminal_mode=True
    e.age_step(t)
   if t==tcancel:
    for e in live:
     if not e.frozen:e.takeover(t)
    cancelled=True
   for e in live:
    if e.frozen:continue
    for x in deferred[id(e)]:heapq.heappush(e.tasks,x)
    if e.tasks and e.tasks[0][0]==t:e.process_tasks(t,maxsrc(t))
   if t==tgrid:
    sign,safety,reason=score_at(t,trades,caps);f,h=policy_pause(day,grid,sign)
    for e in live:
     if not e.frozen:
      e.original_sign=sign;e.decision(t,f if e.policy=='F' else h,maxsrc(t),safety)
    grid+=1
   if t==termtime:
    for e in live:
     if not e.frozen:e.terminal(t,termref)
    done=True
   steps+=1
   if steps%1000==0:budget.guard()
  results=[]
  for e in es:
   r=e.result();r['day']=day;r['terminal_time_capture_ticks']=termtime;r['ledger_file']=day+'-ledger.csv.gz';results.append(r);allresults.append(r)
  save(day+'-summary.json',{'date':day,'p0':str(p0),'q_BTC':str(q),'trade_prefix_count':len(trades),'BBO':quotes.meta,'terminal_capture_ticks':termtime,'terminal_reference_original_row':termref[0],'results':results,'ledger_rows':ledger.rows})
  print(json.dumps({'event':'day_complete','day':day,'paths':len(results),'ledger_rows':ledger.rows,'CPU_seconds':time.process_time()-CPU}),flush=True)
 finally:ledger.close()
''' +s[b:]
# New frozen spec plan paths are outside old next-validation-design; exact identity is in prepare.
s=s.replace("if sha(UNIT/'next-validation-design'/name)!=digest", "if sha(Path(name))!=digest")
p.write_text(s)
