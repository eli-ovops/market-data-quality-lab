"""Independent saved-event accounting audit only; never imports replay/market readers."""
import csv,gzip,json,hashlib,os,time,resource,signal,sys,datetime
from pathlib import Path
from decimal import Decimal as D,getcontext
from collections import Counter
getcontext().prec=60
ROOT=Path(__file__).resolve().parent.parent
OWNER=ROOT/'owner'
START=time.monotonic(); CPU=time.process_time()
T=D(10000000); ZERO=D(0)
def guard(*args):
 if time.process_time()>90:raise TimeoutError('Independent audit CPU90s guard')
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>134217728:raise MemoryError('Independent audit RSS128MiB guard')
 if time.time()>=datetime.datetime(2026,10,22,16,1,37,tzinfo=datetime.timezone.utc).timestamp():raise TimeoutError('Unit UTC deadline')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def eq(a,b,label):
 if a!=b:raise AssertionError((label,str(a),str(b)))
def state():return dict(c=D(5000),q=ZERO,f=ZERO,bn=ZERO,sn=ZERO,bq=ZERO,sq=ZERO,mn=ZERO,tn=ZERO,an=ZERO,af=ZERO,nn=ZERO,nf=ZERO,lots={},due={},nextlot=1,counts=Counter(),last=-1,rows=0,frozen=False,terminal=False,depthcap=None,depth=[],sent=None,trigger=None)
def audit(day):
 path=OWNER/(day+'-ledger.csv.gz');states={};n=0;events=Counter()
 with gzip.open(path,'rt',newline='') as f:
  reader=csv.DictReader(f);header=reader.fieldnames
  for row in reader:
   n+=1
   if n%10000==0:guard()
   key=(row['policy'],row['model'],int(row['delay_ms']));s=states.setdefault(key,state());t=int(row['t']);ev=row['event'];d=json.loads(row['detail'])
   if s['frozen']:raise AssertionError(('post-freeze event',key,ev,t))
   if t<s['last']:raise AssertionError('Path time regression')
   s['last']=t;s['rows']+=1;s['counts'][ev]+=1;events[ev]+=1
   if ev=='fill':
    q=D(d['qty']);p=D(d['fill_price']);fee=D(d['fee']);kind=d['fill_kind'];rate=D('.004') if kind in ('terminal','age_exit') else D('.003');side=row['side'];amount=q*p
    eq(D(d['fee_rate']),rate,'fee rate');eq(fee,amount*rate,'fill fee')
    s['f']+=fee
    if side=='buy':
     s['c']-=amount+fee;s['q']+=q;s['bq']+=q;s['bn']+=amount
     alloc=d['fifo_allocation'];eq(len(alloc),1,'buy single lot');ident=int(alloc[0][0]);eq(ident,s['nextlot'],'lot sequence');s['nextlot']+=1;eq(D(alloc[0][1]),q,'buy allocation');s['lots'][ident]=q;s['due'][ident]=int(d['buy_lot_due']);eq(s['due'][ident],t+10000000,'lot due')
    else:
     s['c']+=amount-fee;s['q']-=q;s['sq']+=q;s['sn']+=amount
     remaining=q;expected=[]
     for ident,v in s['lots'].items():
      take=min(remaining,v)
      if take:s['lots'][ident]-=take;remaining-=take;expected.append((ident,take))
      if not remaining:break
     eq(remaining,ZERO,'FIFO oversell');eq([(int(i),D(v)) for i,v in d['fifo_allocation']],expected,'oldest-first allocation')
    if kind in ('terminal','age_exit'):s['tn']+=amount
    else:s['mn']+=amount
    if kind=='age_exit':
     s['an']+=amount;s['af']+=fee
     if s['sent'] is None:raise AssertionError('Age fill without sent quantity')
     eq(t,s['sent']['arrive'],'arrival time');s['sent']['filled']+=q
    if kind=='terminal':s['nn']+=amount;s['nf']+=fee
    eq(sum(s['lots'].values(),ZERO),s['q'],'independent FIFO total');eq(D(d['lot_remaining_total']),s['q'],'logged FIFO total')
    for u in d['lot_updates']:eq(D(u['remaining']),s['lots'][int(u['id'])],'lot update')
   if ev=='age_trigger':
    s['trigger']=t;eq(int(d['send_at']),t+int(row['delay_ms'])*10000,'cancel barrier delay')
   if ev=='age_exit_sent':
    if s['sent'] is not None:raise AssertionError('Overlapping sent exit')
    eq(t,s['trigger']+int(row['delay_ms'])*10000,'send time')
    alloc=[(int(i),D(v)) for i,v in d['allocation']];expected=[(i,q) for i,q in s['lots'].items() if q and s['due'][i]<=t]
    eq(alloc,expected,'sent due FIFO allocation');q=sum((q for i,q in alloc),ZERO);eq(q,D(d['quantity']),'sent Q');eq(D(d['exit_reserved']),q,'sent reservation');eq(int(d['arrive_at']),t+int(row['delay_ms'])*10000,'second delay');s['sent']={'q':q,'filled':ZERO,'arrive':int(d['arrive_at'])}
   if ev=='age_exit_complete':
    if s['sent'] is None:raise AssertionError('Completion without sent exit')
    eq(s['sent']['filled'],s['sent']['q'],'sent/filled Q');eq(D(d['quantity']),s['sent']['q'],'complete Q');s['sent']=None
   if ev=='exit_depth_reset':
    cap=int(d['reference_capture'])
    if s['depthcap'] is not None and cap<=s['depthcap']:raise AssertionError('Non-new depth reset')
    s['depthcap']=cap;s['depth']=[D(x) for x in d['amounts']];eq(len(s['depth']),25,'depth length')
   if ev=='exit_depth_use':
    eq(int(d['reference_capture']),s['depthcap'],'depth group');i=int(d['level']);before=D(d['before']);used=D(d['used']);after=D(d['after']);eq(before,s['depth'][i],'shared depth before');eq(before-used,after,'depth usage identity')
    if after<0:raise AssertionError('Negative depth')
    s['depth'][i]=after
   if ev=='UNKNOWN_path_frozen':s['frozen']=True
   if ev=='terminal_complete':eq(s['q'],ZERO,'terminal BTC zero');eq(D(row['reserved_BTC']),ZERO,'terminal no reserve');s['terminal']=True
   eq(D(row['cash']),s['c'],'all-row cash');eq(D(row['BTC']),s['q'],'all-row BTC');eq(D(row['fees']),s['f'],'all-row fee');eq(s['c'],D(5000)+s['sn']-s['bn']-s['f'],'independent cumulative cash');eq(s['q'],s['bq']-s['sq'],'independent cumulative BTC')
   if min(D(row['reserved_cash']),D(row['reserved_BTC']),D(row['pending_buy_BTC']),s['c'],s['q'])<0:raise AssertionError('Negative reserve/cash/quantity')
   if D(row['reserved_cash'])>s['c'] or D(row['reserved_BTC'])>s['q']:raise AssertionError('Excess reserve')
 summary=json.loads((OWNER/(day+'-summary.json')).read_text());eq(summary['ledger_rows'],n,'whole ledger denominator');out=[]
 for x in summary['results']:
  key=(x['policy'],x['model'],x['delay_ms']);s=states[key]
  for k,v in [('cash',s['c']),('BTC',s['q']),('fees_USD',s['f']),('maker_notional',s['mn']),('taker_notional',s['tn']),('age_exit_notional',s['an']),('age_exit_fees',s['af']),('terminal_notional',s['nn']),('terminal_fees',s['nf']),('lot_remaining_BTC',sum(s['lots'].values(),ZERO))]:eq(D(x[k]),v,'summary '+k)
  eq(x['frozen'],s['frozen'],'summary frozen');eq(x['counts'].get('fills',0),s['counts']['fill'],'fill denominator')
  if s['frozen']:eq(x['risk_status'],'UNKNOWN_MODEL_RISK','frozen risk');eq(x['inventory_time_scope'],'KNOWN_PREFIX_ONLY','frozen prefix')
  if x['execution_cash_status']=='COMPLETE_CONDITIONAL_MODEL_CASH':
   eq(s['terminal'],True,'full cash requires terminal');eq(D(x['PnL_USD']),s['c']-D(5000),'terminal net cash')
  out.append({'policy':key[0],'model':key[1],'delay_ms':key[2],'rows':s['rows'],'fills':s['counts']['fill'],'terminal':s['terminal'],'frozen':s['frozen'],'cash':str(s['c']),'BTC':str(s['q']),'fees':str(s['f']),'remaining_sent_exit':s['sent'] is not None})
 eq(len(states),8,'paths per day')
 return {'day':day,'compressed_sha256':sha(path),'gzip_EOF_CRC':'PASS full stream','header':header,'rows':n,'event_counts':dict(events),'paths':out,'summary_sha256':sha(OWNER/(day+'-summary.json'))}
def check_result():
 result=json.loads((OWNER/'result.json').read_text());paths=[]
 for day in ('2026-05-01','2026-06-01'):paths.extend(json.loads((OWNER/(day+'-summary.json')).read_text())['results'])
 eq(result['path_results'],paths,'all result paths');eq(len(paths),16,'result denominator');eq(len(result['comparisons']),8,'comparison denominator')
 old=json.loads((ROOT.parents[1]/'economic-correction-20261022'/'owner'/'result.json').read_text())
 for x in result['comparisons']:
  find=lambda policy:next(p for p in paths if p['day']==x['day'] and p['policy']==policy and p['model']==x['model'] and p['delay_ms']==x['delay_ms'])
  f,h=find('F1'),find('H1');fk=f['execution_cash_status']=='COMPLETE_CONDITIONAL_MODEL_CASH';hk=h['execution_cash_status']=='COMPLETE_CONDITIONAL_MODEL_CASH';rk=f['risk_status']==h['risk_status']=='COMPLETE_MODEL_RISK'
  eq(x['F_cash_complete'],fk,'F cash complete');eq(x['H_cash_complete'],hk,'H cash complete');eq(x['complete_cash_comparison'],fk and hk,'paired cash complete');eq(x['risk_complete_both'],rk,'paired risk complete')
  eq(x['F_PnL_USD'],f['PnL_USD'],'F net');eq(x['H_PnL_USD'],h['PnL_USD'],'H net');delta=D(f['PnL_USD'])-D(h['PnL_USD']) if fk and hk else None
  eq(None if x['delta_F_minus_H_USD'] is None else D(x['delta_F_minus_H_USD']),delta,'F-H net')
  keys=('max_inventory_notional_USD','inventory_BTC_seconds','max_drawdown_USD')
  eq(x['F_risk_metrics'],{k:f[k] for k in keys},'F reported risk');eq(x['H_risk_metrics'],{k:h[k] for k in keys},'H reported risk');eq(x['risk_comparable_and_F_not_higher'],all(D(f[k])<=D(h[k]) for k in keys) if rk else None,'reported risk comparison')
  oc=next(c for c in old['comparisons'] if (c['day'],c['model'],c['delay_ms'])==(x['day'],x['model'],x['delay_ms']))
  for pol,p,known in (('F',f,fk),('H',h,hk)):
   eq(x[pol+'0_PnL_USD'],oc[pol+'_PnL_USD'],'old cash read-only identity');v=D(p['PnL_USD'])-D(oc[pol+'_PnL_USD']) if known else None
   eq(None if x[pol+'1_minus_'+pol+'0_USD'] is None else D(x[pol+'1_minus_'+pol+'0_USD']),v,'new-old cash scalar')
  eq(x['old_new_matched_price_risk'],'UNKNOWN','old-new risk limit')
  fail=(fk and D(f['PnL_USD'])<=0) or (fk and hk and delta<=0)
  if fail:eq(x['status'],'CASH_NECESSARY_CONDITION_NOT_PASSED','cash independent failure')
  if x['status']=='MODEL_CONDITIONAL_CELL_PASS':eq(fk and hk and rk and not fail and x['risk_comparable_and_F_not_higher'],True,'candidate full requirements')
 eq(result['has_execution_cash_unknown'],any(not c['complete_cash_comparison'] for c in result['comparisons']),'global cash unknown');eq(result['has_risk_unknown'],any(not c['risk_complete_both'] for c in result['comparisons']),'global risk unknown')
 return {'result_sha256':sha(OWNER/'result.json'),'paths':16,'comparisons':8,'status':result['status'],'comparison_scalar_consistency':'PASS; risk values compared only, not recomputed'}
def main():
 resource.setrlimit(resource.RLIMIT_CPU,(90,91));signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,1,1)
 out={'status':'STARTED','pid':os.getpid(),'scope':'saved ledger only; no engine, market reader, signals, prices, risk recomputation or replay','days':[]}
 try:
  for day in ('2026-05-01','2026-06-01'):out['days'].append(audit(day))
  out['result_checks']=check_result();out['status']='PASS_SAVED_EVENT_ACCOUNTING';code=0
 except BaseException as e:out['status']='AUDIT_FAILED_NO_RETRY';out['error']=repr(e);code=1
 signal.setitimer(signal.ITIMER_REAL,0);out.update(CPU_seconds=time.process_time(),wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,exit_code=code)
 (ROOT/'review'/'ledger-audit-receipt.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('status','pid','CPU_seconds','wall_seconds','peak_RSS_bytes','exit_code')},ensure_ascii=False));return code
if __name__=='__main__':sys.exit(main())
