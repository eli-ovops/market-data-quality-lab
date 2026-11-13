"""One saved-ledger accounting reduction. Never imports or executes Owner code."""
import csv,gzip,io,json,hashlib,time,resource,signal,sys,os
from pathlib import Path
from decimal import Decimal,getcontext
from collections import Counter
from datetime import datetime,timezone
getcontext().prec=60
D=Decimal;Z=D(0);ONE=D(1);SLIP=D('.0001')
OUT=Path(__file__).resolve().parent;OWNER=OUT.parents[1]/'owner';ROOT=OUT.parent/'root'
C=time.process_time();W=time.monotonic();coverage={}
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):
 with (OUT/n).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2,default=str);f.write('\n')
def guard(*a):
 if time.process_time()-C>=49:raise TimeoutError('CPU49 guard/hard50')
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>134217728:raise MemoryError('RSS128MiB')
 if datetime.now(timezone.utc)>=datetime.fromisoformat('2026-10-22T15:45:58.036731+00:00'):raise TimeoutError('deadline')
 if sum(x.stat().st_size for x in OUT.iterdir() if x.is_file())>8388608:raise OSError('output8MiB')
class HashRead:
 def __init__(self,f):self.f=f;self.h=hashlib.sha256();self.n=0
 def read(self,n=-1):
  b=self.f.read(n);self.h.update(b);self.n+=len(b);return b
 def tell(self):return self.f.tell()
def main():
 resource.setrlimit(resource.RLIMIT_CPU,(50,51));signal.signal(signal.SIGXCPU,guard)
 scope=json.loads((ROOT/'scope.json').read_text())
 if sha(OWNER/'result.json')!=scope['source_result_sha256'] or sha(OWNER/'final-manifest.json')!=scope['source_manifest_sha256']:raise ValueError('source scope drift')
 manifest=json.loads((OWNER/'final-manifest.json').read_text());mi=manifest['files']
 if not isinstance(mi,dict):raise ValueError('manifest files must be filename-keyed dict')
 sums={d:json.loads((OWNER/(d+'-summary.json')).read_text()) for d in ('2026-05-01','2026-06-01')}
 identities=[];states={}
 for day,sm in sums.items():
  name=day+'-summary.json'
  if sha(OWNER/name)!=mi[name]['sha256']:raise ValueError('summary hash drift')
  for sr in sm['results']:
   states[(day,sr['model'],str(sr['delay_ms']),sr['policy'])]={'sr':sr,'rows':0,'fills':0,'groups':{},'buy_notional':Z,'sell_notional':Z,'buy_qty':Z,'sell_qty':Z,'fees':Z,'execution_available':Z,'mid_empty_count':0,'last':None,'first_fill':None,'first_fill_each_group':{},'last_fill':None}
 save('started.json',{'utc':utc(),'pid':os.getpid(),'script_sha256':sha(Path(__file__)),'scope_sha256':sha(ROOT/'scope.json'),'source_result_sha256':sha(OWNER/'result.json'),'source_manifest_sha256':sha(OWNER/'final-manifest.json'),'source_summary_sha256':{d:sha(OWNER/(d+'-summary.json')) for d in sums},'expected_ledgers':[dict(path=str(OWNER/(d+'-ledger.csv.gz')),**mi[d+'-ledger.csv.gz']) for d in sums],'method':'One pass per saved ledger, all16paths incl frozen prefixes. Exact original side/kind groups. Saved mid only (freshness unknown); buy q*(m-p), sell q*(p-m). Full G=N+fees only when old N nonnull, and attribution UNKNOWN stays UNKNOWN. Fixed exit adverse item=notional*.0001/.9999, an accounting component, never a changed trade/fee/PnL path.'})
 with gzip.open(OUT/'fill-accounting-audit.csv.gz','wt',newline='') as af:
  writer=csv.writer(af);writer.writerow(['day','ledger_row','t','model','delay_ms','policy','side','kind','qty','fill_price','notional','fee','saved_mid','saved_mid_execution_term','fixed_exit_adverse_item','saved_running_execution_term','saved_running_inventory_term'])
  for day,sm in sums.items():
   lp=OWNER/(day+'-ledger.csv.gz');n=0;fc=0
   with lp.open('rb') as raw:
    h=HashRead(raw)
    with gzip.GzipFile(fileobj=h,mode='rb') as gz,io.TextIOWrapper(gz,newline='') as txt:
     rd=csv.reader(txt);head=next(rd);ix={k:i for i,k in enumerate(head)}
     for n,r in enumerate(rd,1):
      key=(day,r[ix['model']],r[ix['delay_ms']],r[ix['policy']]);s=states[key];s['rows']+=1
      s['last']={'t':r[ix['t']],'event':r[ix['event']],'cash':r[ix['cash']],'BTC':r[ix['BTC']],'fees':r[ix['fees']],'execution_price_term':r[ix['execution_price_term']],'inventory_price_term':r[ix['inventory_price_term']],'mid_reference':r[ix['mid_reference']]}
      if r[ix['event']]=='fill':
       dt=json.loads(r[ix['detail']]);kind=dt['fill_kind'];side=r[ix['side']]
       if kind not in ('equal','cross','age_exit','terminal') or (kind in ('age_exit','terminal') and side!='sell'):raise ValueError('unexpected side/kind')
       q=D(dt['qty']);p=D(dt['fill_price']);fee=D(dt['fee']);notional=q*p;m=r[ix['mid_reference']];exec_term=None if not m else q*((D(m)-p) if side=='buy' else (p-D(m)))
       adverse=notional*SLIP/(ONE-SLIP) if kind in ('age_exit','terminal') else Z
       gname=('maker_'+side+'_'+kind) if kind in ('equal','cross') else kind+'_sell'
       g=s['groups'].setdefault(gname,{'fills':0,'qty':Z,'notional':Z,'fee':Z,'execution_from_nonempty_saved_mid':Z,'mid_empty_count':0,'fixed_exit_adverse_item':Z})
       g['fills']+=1;g['qty']+=q;g['notional']+=notional;g['fee']+=fee;g['fixed_exit_adverse_item']+=adverse
       s['fills']+=1;fc+=1;s[side+'_notional']+=notional;s[side+'_qty']+=q;s['fees']+=fee
       if exec_term is None:g['mid_empty_count']+=1;s['mid_empty_count']+=1
       else:g['execution_from_nonempty_saved_mid']+=exec_term;s['execution_available']+=exec_term
       witness={'ledger_row':n,'t':r[ix['t']],'side':side,'kind':kind,'qty':str(q),'price':str(p),'fee':str(fee),'saved_mid':m,'saved_mid_freshness':'UNKNOWN','execution_from_saved_mid':str(exec_term) if exec_term is not None else None,'fixed_exit_adverse_item':str(adverse)}
       if s['first_fill'] is None:s['first_fill']=witness
       s['first_fill_each_group'].setdefault(gname,witness);s['last_fill']=witness
       writer.writerow([day,n,r[ix['t']],key[1],key[2],key[3],side,kind,q,p,notional,fee,m,exec_term,adverse,r[ix['execution_price_term']],r[ix['inventory_price_term']]])
      if n%4096==0:coverage[day]={'rows':n,'fills':fc};guard()
   coverage[day]={'rows':n,'fills':fc}
   if h.h.hexdigest()!=mi[lp.name]['sha256'] or h.n!=mi[lp.name]['bytes']:raise ValueError('ledger SHA/length drift')
   if n!=sm['ledger_rows']:raise ValueError('ledger row denominator')
   identities.append({'day':day,'path':str(lp),'bytes':h.n,'sha256':h.h.hexdigest(),'gzip_EOF_CRC':True,'rows':n,'fills':fc})
   guard()
 paths=[]
 expected_groups=['maker_buy_equal','maker_buy_cross','maker_sell_equal','maker_sell_cross','age_exit_sell','terminal_sell']
 for key,s in sorted(states.items()):
  sr=s['sr'];last=s['last'];full=sr['execution_cash_status']=='COMPLETE_CONDITIONAL_MODEL_CASH';N=None if sr['PnL_USD'] is None else D(sr['PnL_USD']);G=None if N is None else N+s['fees'];attr=sr['attribution'];adverse=sum((g['fixed_exit_adverse_item'] for g in s['groups'].values()),Z)
  if s['fees']!=D(sr['fees_USD']) or s['fills']!=sr['counts'].get('fills',0) or D(last['cash'])!=D(sr['cash']) or D(last['BTC'])!=D(sr['BTC']):raise ValueError('fill accounting vs original summary')
  execres=s['execution_available']-D(last['execution_price_term'])
  if execres!=0:raise ValueError('execution sum vs saved running term')
  grossres=None;attrres=None
  if full:
   if N is None or D(last['BTC'])!=0 or s['buy_qty']!=s['sell_qty']:raise ValueError('complete cash not flat')
   grossres=s['sell_notional']-s['buy_notional']-G
   if grossres!=0:raise ValueError('gross cash identity')
  if attr is not None:
   if G is None:raise ValueError('valid attribution but G missing')
   attrres=D(attr['inventory_price'])+D(attr['execution_price'])-G
   if attrres!=0 or D(attr['execution_price'])!=s['execution_available']:raise ValueError('attribution identity')
  for g in s['groups'].values():g['execution_plus_fixed_exit_item_NOT_ALPHA']=None if g['mid_empty_count'] else g['execution_from_nonempty_saved_mid']+g['fixed_exit_adverse_item']
  path={'day':key[0],'model':key[1],'delay_ms':int(key[2]),'policy':key[3],'scope':'COMPLETE_SAVED_MODEL_CASH_PATH' if full else 'FROZEN_SAVED_PREFIX_NOT_FULL_PNL','rows':s['rows'],'fills':s['fills'],'groups':{n:s['groups'].get(n,{'fills':0,'qty':Z,'notional':Z,'fee':Z,'execution_from_nonempty_saved_mid':Z,'mid_empty_count':0,'fixed_exit_adverse_item':Z,'execution_plus_fixed_exit_item_NOT_ALPHA':Z}) for n in expected_groups},'actual_buy_notional':s['buy_notional'],'actual_sell_notional':s['sell_notional'],'buy_qty':s['buy_qty'],'sell_qty':s['sell_qty'],'original_N_USD':N,'explicit_fees_USD':s['fees'],'G_equals_N_plus_fees_USD':G,'G_over_actual_buy_notional_bp':G/s['buy_notional']*10000 if G is not None and s['buy_notional'] else None,'sell_minus_buy_minus_G_residual':grossres,'old_attribution_status':sr['attribution_status'],'old_attribution_UNCHANGED':attr,'inventory_plus_execution_minus_G_residual':attrres,'saved_mid_empty_fill_count':s['mid_empty_count'],'saved_mid_freshness':'UNKNOWN (no market data read)','execution_sum_from_nonempty_saved_mid':s['execution_available'],'execution_vs_saved_running_term_residual':execres,'fixed_exit_adverse_item_USD':adverse,'execution_plus_fixed_exit_item_NOT_ALPHA':s['execution_available']+adverse if not s['mid_empty_count'] else None,'saved_last_record':last,'first_fill':s['first_fill'],'first_fill_each_group':s['first_fill_each_group'],'last_fill':s['last_fill'],'original_risk_status_UNCHANGED':sr['risk_status'],'frozen_UNCHANGED':sr.get('frozen')}
  paths.append(path)
 cells=[]
 for day in sums:
  for model in ('E','X'):
   for ms in (100,500):
    f=next(p for p in paths if (p['day'],p['model'],p['delay_ms'],p['policy'])==(day,model,ms,'F1'));h=next(p for p in paths if (p['day'],p['model'],p['delay_ms'],p['policy'])==(day,model,ms,'H1'));known=f['G_equals_N_plus_fees_USD'] is not None and h['G_equals_N_plus_fees_USD'] is not None
    def small(p):return {k:p[k] for k in ['scope','original_N_USD','explicit_fees_USD','G_equals_N_plus_fees_USD','actual_buy_notional','G_over_actual_buy_notional_bp','old_attribution_status','old_attribution_UNCHANGED','fixed_exit_adverse_item_USD','execution_plus_fixed_exit_item_NOT_ALPHA']}
    cells.append({'day':day,'model':model,'delay_ms':ms,'scope':'COMPLETE_CASH_COMPARISON' if known else 'UNKNOWN_FROZEN_PREFIX','F1':small(f),'H1':small(h),'delta_N_F1_minus_H1_USD':f['original_N_USD']-h['original_N_USD'] if known else None,'delta_G_F1_minus_H1_USD':f['G_equals_N_plus_fees_USD']-h['G_equals_N_plus_fees_USD'] if known else None,'normalization_limit':'each path own executed buy notional; not matched activity/risk, causality, significance or alternative fee result'})
 if len(paths)!=16 or len(cells)!=8:raise ValueError('path/cell denominator')
 save('summary-16paths.json',{'status':'COMPLETE_SAVED_ACCOUNTING_REDUCTION','paths':paths,'inputs':identities,'coverage':coverage,'total_paths':16,'complete_cash_paths':sum(p['scope']=='COMPLETE_SAVED_MODEL_CASH_PATH' for p in paths),'frozen_prefix_paths':sum(p['scope']!='COMPLETE_SAVED_MODEL_CASH_PATH' for p in paths),'mid_freshness':'UNKNOWN for all; nonempty does not imply synchronous/fresh','claim':'saved bookkeeping decomposition only, not isolated signal alpha or new counterfactual PnL'})
 save('comparison-8cells.json',{'cells':cells,'complete_cash_cells':sum(c['scope']=='COMPLETE_CASH_COMPARISON' for c in cells),'unknown_cells':sum(c['scope']!='COMPLETE_CASH_COMPARISON' for c in cells)})
if __name__=='__main__':
 status='FAILED_STOP';code=1;err=None
 try:main();status='COMPLETE_SAVED_ACCOUNTING_REDUCTION';code=0
 except BaseException as e:err={'type':type(e).__name__,'message':str(e)}
 finally:save('completion.json',{'utc':utc(),'pid':os.getpid(),'status':status,'exit_code':code,'error':err,'CPU_seconds':time.process_time()-C,'wall_seconds':time.monotonic()-W,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'coverage':coverage,'script_sha256':sha(Path(__file__)),'output_bytes_before_receipt':sum(x.stat().st_size for x in OUT.iterdir() if x.is_file()),'threads':1,'network':0,'actual_route':'UNKNOWN','one_saved_ledger_reduction_not_engine_replay':True})
 sys.exit(code)
