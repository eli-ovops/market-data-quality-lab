"""Single descriptive reduction of sealed ledgers; never imports strategy/reader."""
import csv,gzip,json,time,resource,hashlib,sys,os,signal
from pathlib import Path
from collections import Counter,defaultdict
from decimal import Decimal,getcontext
from datetime import datetime,timezone
getcontext().prec=60
D=Decimal;T=10000000;Z=D(0)
OUT=Path(__file__).resolve().parent;UNIT=OUT.parents[1]
OWNER=UNIT/'economic-correction-20261022'/'owner'; ROOT=OUT.parent/'root'
C0=time.process_time();W0=time.monotonic();progress={};states={}
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (OUT/n).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2,default=str);f.write('\n')
def guard(*a):
 if time.process_time()-C0>=39:raise TimeoutError('CPU39 guard/hard40')
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>134217728:raise MemoryError('RSS128MiB')
 if datetime.now(timezone.utc)>=datetime.fromisoformat('2026-10-22T12:44:34.788221+00:00'):raise TimeoutError('active deadline')
 if sum(f.stat().st_size for f in OUT.iterdir() if f.is_file())>4194304:raise OSError('output4MiB')
class HashRead:
 def __init__(self,f):self.f=f;self.h=hashlib.sha256();self.n=0
 def read(self,n=-1):
  b=self.f.read(n);self.h.update(b);self.n+=len(b);return b
 def tell(self):return self.f.tell()
def snap(r,ix):return {k:r[ix[k]] for k in ('t','event','policy','model','delay_ms','order_id','side','quantity','leaves','BTC','fees','detail')}
def main():
 import io
 resource.setrlimit(resource.RLIMIT_CPU,(40,41));signal.signal(signal.SIGXCPU,guard)
 auth=json.loads((ROOT/'authorization.json').read_text());manifest=json.loads((OWNER/'final-manifest.json').read_text());mi={x['path']:x for x in manifest['files']}
 auditpath=UNIT/'economic-correction-20261022'/'review'/'saved-ledger-audit.json';audit=json.loads(auditpath.read_text())
 summary={day:json.loads((OWNER/(day+'-summary.json')).read_text()) for day in ('2026-05-01','2026-06-01')}
 save('started.json',{'utc':utc(),'pid':os.getpid(),'script_sha256':sha(Path(__file__)),'authorization_sha256':sha(ROOT/'authorization.json'),'brief_sha256':sha(ROOT/'brief.md'),'owner_manifest_sha256':sha(OWNER/'final-manifest.json'),'previous_full_ledger_audit_sha256':sha(auditpath),'expected_inputs':[mi[day+'-ledger.csv.gz'] for day in summary],'method':'One chronological per-path reduction of existing rows only. No engine/reader imports, no market reads, no new orders/positions/labels/risk/PnL. Inventory intervals use previous saved BTC until next saved timestamp. Last1s=(terminal-1s,terminal], before terminal fills. Cancelling fills classified by saved cancel_sent/cancel_at and ledger order. All16paths, no window selection.'})
 for day,ds in summary.items():
  for sr in ds['results']:
   k=(day,sr['model'],str(sr['delay_ms']),sr['policy']);q=D(sr['q_BTC'])
   states[k]={'original':sr,'q':q,'events':Counter(),'cancel_reasons':Counter(),'accepted_outcomes':Counter(),'orders':{},'fill_groups':{},'inflight':{'rows':0,'qty':Z,'fee':Z,'request_same_time_rows':0,'effective_same_time_rows':0},'prev_t':None,'prev_btc':Z,'prev_text':None,'integral_ticks':Z,'duration':Counter(),'max_btc':Z,'positive_start':None,'longest_ticks':0,'first_t':None,'last_t':None,'terminal_t':int(sr['terminal_time_capture_ticks']),'preterminal_btc':None,'recent_buy_qty':Z,'last_maker_buy_t':None,'last_maker_sell_t':None,'first_event':None,'first_fill':None,'first_cancel':None,'first_inflight_fill':None,'terminal_first_fill':None,'terminal_complete':None,'rows':0}
 inputrecords=[]
 for day,ds in summary.items():
  lp=OWNER/(day+'-ledger.csv.gz');n=0;h=None
  with lp.open('rb') as raw:
   h=HashRead(raw)
   with gzip.GzipFile(fileobj=h,mode='rb') as gz,io.TextIOWrapper(gz,newline='') as txt:
    reader=csv.reader(txt);head=next(reader);ix={x:i for i,x in enumerate(head)}
    for n,r in enumerate(reader,1):
     k=(day,r[ix['model']],r[ix['delay_ms']],r[ix['policy']]);s=states[k];t=int(r[ix['t']]);ev=r[ix['event']];s['rows']+=1;s['events'][ev]+=1
     if s['first_t'] is None:s['first_t']=t;s['first_event']=snap(r,ix)
     if s['prev_t'] is not None:
      dt=t-s['prev_t']
      if dt<0:raise ValueError('perpath time inversion')
      btc=s['prev_btc'];s['integral_ticks']+=btc*dt
      s['duration']['zero' if btc==0 else 'positive_lt_q' if btc<s['q'] else 'at_least_q']+=dt
      if s['positive_start'] is not None:s['longest_ticks']=max(s['longest_ticks'],t-s['positive_start'])
     if r[ix['BTC']]!=s['prev_text']:
      newbtc=D(r[ix['BTC']]);s['prev_text']=r[ix['BTC']]
     else:newbtc=s['prev_btc']
     if s['prev_btc']==0 and newbtc>0:s['positive_start']=t
     if newbtc==0:s['positive_start']=None
     s['max_btc']=max(s['max_btc'],newbtc);s['last_t']=t
     oid=r[ix['order_id']]
     if ev=='accepted':s['orders'][oid]={'filled':Z,'qty':D(r[ix['quantity']])}
     if ev=='cancel_sent':
      detail=json.loads(r[ix['detail']]);s['cancel_reasons'][detail.get('reason','UNKNOWN')]+=1
      if s['first_cancel'] is None:s['first_cancel']=snap(r,ix)
     if ev=='fill':
      detail=json.loads(r[ix['detail']]);qty=D(detail['qty']);price=D(detail['fill_price']);fee=D(detail['fee']);kind=detail['fill_kind'];side=r[ix['side']]
      fk=side+'|'+kind;fg=s['fill_groups'].setdefault(fk,{'rows':0,'qty':Z,'notional':Z,'fee':Z});fg['rows']+=1;fg['qty']+=qty;fg['notional']+=qty*price;fg['fee']+=fee
      if s['first_fill'] is None:s['first_fill']=snap(r,ix)
      if kind=='terminal':
       if s['preterminal_btc'] is None:s['preterminal_btc']=s['prev_btc'];s['terminal_first_fill']=snap(r,ix)
      else:
       s['last_maker_'+side+'_t']=t
       if side=='buy' and s['terminal_t']-T<t<=s['terminal_t']:s['recent_buy_qty']+=qty
       if oid not in s['orders']:raise ValueError('maker fill has no accepted log')
       s['orders'][oid]['filled']+=qty
       cs=int(r[ix['cancel_sent']] or 0);ca=int(r[ix['cancel_at']] or 0)
       if cs and cs<=t<=ca:
        a=s['inflight'];a['rows']+=1;a['qty']+=qty;a['fee']+=fee;a['request_same_time_rows']+=t==cs;a['effective_same_time_rows']+=t==ca
        if s['first_inflight_fill'] is None:s['first_inflight_fill']=snap(r,ix)
       if D(r[ix['leaves']])==0:
        o=s['orders'].pop(oid);s['accepted_outcomes']['full']+=1
     if ev=='cancel_effective' and oid in s['orders']:
      o=s['orders'].pop(oid);s['accepted_outcomes']['none' if o['filled']==0 else 'partial']+=1
     if ev=='terminal_complete':s['terminal_complete']=snap(r,ix)
     s['prev_t']=t;s['prev_btc']=newbtc
     if n%4096==0:progress[day]=n;guard()
  progress[day]=n
  if h.h.hexdigest()!=mi[lp.name]['sha256'] or h.n!=mi[lp.name]['bytes']:raise ValueError('compressed ledger SHA/bytes drift')
  if n!=ds['ledger_rows']:raise ValueError('ledger count drift')
  prior=next(x for x in audit['days'] if x['day']==day)
  if n!=prior['all_rows_checked']:raise ValueError('previous audit count mismatch')
  inputrecords.append({'date':day,'path':str(lp),'bytes':h.n,'sha256':h.h.hexdigest(),'gzip_EOF_CRC':True,'all_rows':n,'matches_previous_audit_rows':True})
  guard()
 out=[]
 mapping={'submit':'submitted','accepted':'accepted','cancel_sent':'cancel_sent','cancel_effective':'cancel_effective','reject_reference_missing':'reject_reference_missing','reject_post_only':'reject_post_only','grid':'decision_grids','fill':'fills'}
 for k,s in sorted(states.items()):
  sr=s['original'];checks={v:{'reduced':s['events'][a],'original':sr['counts'].get(v,0),'match':s['events'][a]==sr['counts'].get(v,0)} for a,v in mapping.items()}
  if not all(x['match'] for x in checks.values()):raise ValueError('summary count mismatch')
  if s['orders']:raise ValueError('accepted orders unclosed')
  integ=s['integral_ticks']/T;longest=D(s['longest_ticks'])/T
  if integ!=D(sr['inventory_BTC_seconds']) or longest!=D(sr['longest_positive_inventory_seconds']):raise ValueError('saved inventory identity mismatch')
  term=s['fill_groups'].get('sell|terminal',{'rows':0,'qty':Z,'notional':Z,'fee':Z});pre=s['preterminal_btc'] if s['preterminal_btc'] is not None else Z
  if term['notional']!=D(sr['taker_notional']) or term['fee']!=term['notional']*D('.004') or term['qty']!=pre or s['prev_btc']!=0:raise ValueError('terminal saved accounting mismatch')
  if sum(s['accepted_outcomes'].values())!=s['events']['accepted']:raise ValueError('accepted outcome denominator')
  out.append({'day':k[0],'model':k[1],'delay_ms':int(k[2]),'policy':k[3],'q_BTC':s['q'],'rows':s['rows'],'event_counts':dict(s['events']),'count_checks':checks,'cancel_sent_reasons':dict(s['cancel_reasons']),'accepted_order_outcomes':dict(s['accepted_outcomes']),'accepted_outcome_denominator':s['events']['accepted'],'fills_by_side_kind':s['fill_groups'],'cancel_inflight_saved_maker_fills':s['inflight'],'inventory':{'first_t':s['first_t'],'last_t':s['last_t'],'interval_seconds':{a:D(b)/T for a,b in s['duration'].items()},'max_BTC':s['max_btc'],'quantity_time_BTC_seconds':integ,'matches_original_inventory_integral':True,'longest_positive_interval_seconds':longest,'matches_original_longest_positive':True,'preterminal_BTC':pre,'preterminal_q_multiple':pre/s['q'],'last_maker_buy_t':s['last_maker_buy_t'],'last_maker_sell_t':s['last_maker_sell_t'],'recent1s_maker_buy_qty':s['recent_buy_qty'],'terminal_at_least1s_qty_lower_bound':max(Z,pre-s['recent_buy_qty'])},'terminal':term,'terminal_zero_BTC':True,'witnesses':{a:s[a] for a in ('first_event','first_fill','first_cancel','first_inflight_fill','terminal_first_fill','terminal_complete')},'risk_status_unchanged':sr['risk_status'],'old_PnL_USD_reference_only':sr['PnL_USD']})
 comps=[]
 for day in summary:
  for model in ('E','X'):
   for ms in (100,500):
    f=next(x for x in out if (x['day'],x['model'],x['delay_ms'],x['policy'])==(day,model,ms,'F'));h=next(x for x in out if (x['day'],x['model'],x['delay_ms'],x['policy'])==(day,model,ms,'H'))
    def small(x):return {a:x[a] for a in ('event_counts','cancel_sent_reasons','accepted_order_outcomes','fills_by_side_kind','cancel_inflight_saved_maker_fills','inventory','terminal','old_PnL_USD_reference_only')}
    comps.append({'day':day,'model':model,'delay_ms':ms,'F':small(f),'H':small(h),'claim':'paired descriptive saved-record comparison; no counterfactual or independent net-profit evidence'})
 save('summary-16paths.json',{'status':'COMPLETE_SAVED_RECORD_REDUCTION','paths':out,'input_records':inputrecords,'all_paths':16,'all_cells':8,'count_unit':'parallel simulated paths; events/order IDs may repeat across scenarios','limitations':'1s quantity-age is conservation lower bound, not FIFO cost/holding attribution. Inventory intervals are aggregate positive-balance periods, not per-coin/order ages. Inflight fills are model records; un-cancelled counterfactual UNKNOWN. No new risk or PnL calculation.'})
 save('comparison-8cells.json',{'cells':comps})
if __name__=='__main__':
 status='FAILED_STOP';code=1;err=None
 try:main();status='COMPLETE_SAVED_RECORD_REDUCTION';code=0
 except BaseException as e:err={'type':type(e).__name__,'message':str(e)}
 finally:save('completion.json',{'utc':utc(),'pid':os.getpid(),'status':status,'exit_code':code,'error':err,'CPU_seconds':time.process_time()-C0,'wall_seconds':time.monotonic()-W0,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'rows_covered':progress,'script_sha256':sha(Path(__file__)),'output_bytes_before_receipt':sum(f.stat().st_size for f in OUT.iterdir() if f.is_file()),'threads':1,'network':0,'actual_model_effort':'UNKNOWN','no_engine_or_reader_import':True,'no_new_orders_risk_or_PnL':True})
 sys.exit(code)
