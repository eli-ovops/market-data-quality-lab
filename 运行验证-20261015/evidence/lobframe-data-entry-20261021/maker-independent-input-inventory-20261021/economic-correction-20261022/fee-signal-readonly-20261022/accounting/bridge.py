"""One fixed-path JSON scalar accounting bridge; no replay/market reader or engine import."""
import os,sys,json,hashlib,time,resource,signal
from pathlib import Path
from decimal import Decimal,getcontext
from datetime import datetime,timezone
getcontext().prec=60
D=Decimal;OUT=Path(__file__).resolve().parent;UNIT=OUT.parent.parent
BOOT=time.monotonic()
EXPECTED={'owner/result.json':'fd9c510127231b967b9c934d963ccedd20efdf6f941a267b1c5bd9b17c5117d2','review/saved-ledger-audit.json':'40a4e1c8fb2263d9c2993f4d1fdd3573f152576938d41fff36370b4688d9d2c1','owner/final-manifest.json':'826686320f6c044a5d2996d7703465d596bc1ff241315b4d7e01f1d9e577aa69'}
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
 with (OUT/n).open('x') as f:json.dump(x,f,ensure_ascii=True,indent=2);f.write('\n')
def guard(*args):
 if time.process_time()>=9.5 or time.monotonic()-BOOT>=10:raise TimeoutError('10s analysis cap')
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>134217728:raise MemoryError('128MiB RSS')
 if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2097152:raise OSError('2MiB output')
def cellkey(x):return (x['day'],x['model'],int(x['delay_ms']),x['policy'])
def main():
 save('started.json',{'utc':utc(),'pid':os.getpid(),'executable':sys.executable,'version':sys.version,'script_sha256':sha(__file__),'argv':sys.argv,'maximum_formal_scalar_analyses':1})
 resource.setrlimit(resource.RLIMIT_CPU,(10,11));signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,1,1)
 sources={};status='FAILED_STOP'
 try:
  for name,h in EXPECTED.items():
   actual=sha(UNIT/name)
   if actual!=h:raise ValueError('Frozen small input identity mismatch:'+name)
   sources[name]=actual
  acceptance=json.loads((UNIT/'root'/'acceptance.json').read_text());sources['root/acceptance.json']=sha(UNIT/'root'/'acceptance.json')
  if acceptance['status']!='ACCEPTED_WITH_LIMITS':raise ValueError('Prior full audit not accepted')
  accepted={Path(x['path']).relative_to(UNIT).as_posix():x['sha256'] for x in acceptance['bound_artifacts']}
  for name in ('owner/result.json','review/saved-ledger-audit.json'):
   if accepted[name]!=EXPECTED[name]:raise ValueError('Acceptance binding mismatch')
  manifest=json.loads((UNIT/'owner'/'final-manifest.json').read_text());mh={r['path']:r['sha256'] for r in manifest['files']}
  result=json.loads((UNIT/'owner'/'result.json').read_text());audit=json.loads((UNIT/'review'/'saved-ledger-audit.json').read_text())
  if audit['status']!='PASS_SAVED_ACCOUNTING_AND_REPORTED_STATE_CONSISTENCY':raise ValueError('Independent full saved-ledger audit not PASS')
  summaries={}
  for day in ('2026-05-01','2026-06-01'):
   name=day+'-summary.json';p=UNIT/'owner'/name;h=sha(p)
   if h!=mh[name]:raise ValueError('Summary frozen identity mismatch')
   sources['owner/'+name]=h
   for r in json.loads(p.read_text())['results']:summaries[cellkey(r)]=r
  witnesses={}
  for day in audit['days']:
   if not day['all_summary_balances_matched']:raise ValueError('Audit balances not matched')
   for w in day['all_terminal_complete_witnesses']:
    key=(day['day'],w['model'],int(w['delay_ms']),w['policy'])
    if key in witnesses:raise ValueError('Duplicate terminal witness')
    witnesses[key]=w
  paths={}
  for r in result['path_results']:
   key=cellkey(r);s=summaries[key];w=witnesses[key]
   if r['execution_cash_status']!='COMPLETE_CONDITIONAL_MODEL_CASH' or D(r['BTC'])!=0:raise ValueError('Incomplete execution/terminal cash')
   N=D(r['PnL_USD']);C=D(r['fees_USD']);cash=D(r['cash'])
   if N!=D(s['PnL_USD']) or C!=D(s['fees_USD']) or cash!=D(s['cash']):raise ValueError('Result vs summary')
   if N!=D(w['cash'])-5000 or C!=D(w['fees']) or D(w['BTC'])!=0:raise ValueError('Independent terminal witness mismatch')
   maker=D(r['maker_notional'])*D('.003');terminal=D(r['taker_notional'])*D('.004')
   if maker+terminal!=C:raise ArithmeticError('Notional fee split not exact')
   G=N+C
   paths[key]={'day':r['day'],'model':r['model'],'delay_ms':r['delay_ms'],'policy':r['policy'],'N_USD':str(N),'C_explicit_fees_USD':str(C),'G_fixed_path_addback_USD':str(G),'maker_fee_USD':str(maker),'terminal_taker_fee_USD':str(terminal),'G_minus_C_minus_N_residual':'0','same_fixed_path_fee_budget_for_N_zero_USD':str(G),'any_nonnegative_total_fee_can_allow_positive_fixed_path_N':G>0,'cash_status':r['execution_cash_status'],'risk_status':r['risk_status'],'attribution_status':r['attribution_status'],'independent_terminal_witness_verified':True}
  if len(paths)!=16 or len(witnesses)!=16 or len(summaries)!=16:raise ValueError('Fixed16 paths')
  rows=[]
  for day in ('2026-05-01','2026-06-01'):
   for model in ('E','X'):
    for ms in (100,500):
     f=paths[(day,model,ms,'F')];h=paths[(day,model,ms,'H')]
     dg=D(f['G_fixed_path_addback_USD'])-D(h['G_fixed_path_addback_USD']);dc=D(f['C_explicit_fees_USD'])-D(h['C_explicit_fees_USD']);dn=D(f['N_USD'])-D(h['N_USD'])
     if dg-dc!=dn:raise ArithmeticError('Delta bridge identity')
     original=next(x for x in result['comparisons'] if x['day']==day and x['model']==model and x['delay_ms']==ms)
     if D(original['delta_F_minus_H_USD'])!=dn:raise ValueError('Saved comparison delta mismatch')
     rows.append({'day':day,'model':model,'delay_ms':ms,'F':f,'H':h,'delta_G_USD':str(dg),'delta_C_USD':str(dc),'delta_N_USD':str(dn),'delta_identity_residual':'0'})
  save('bridge.json',{'status':'COMPLETE_FIXED_PATH_ACCOUNTING_BRIDGE_NOT_ZERO_FEE_STRATEGY','definitions':{'N':'saved complete conditional-model PnL_USD','C':'saved explicit maker+terminal taker fees_USD','G':'N+C, fixed saved fills/capital/positions only; includes inventory/execution and original depth/slip','delta_identity':'deltaN=deltaG-deltaC'},'fixed_denominators':{'paths':16,'comparisons':8},'rows':rows,'source_sha256':sources,'risk':'UNKNOWN_ALL_PATHS_UNCHANGED','attribution':'UNKNOWN_ALL_PATHS_UNCHANGED','no_personal_profit_or_pure_alpha_claim':True,'no_replay_or_new_fee_strategy':True})
  lines=['# 固定路径费用会计桥（不是零费率策略）','', 'N=已存完整模型净额；C=显式手续费；G=N+C。下表全部为USD，展示4位，精确Decimal见bridge.json。8格全部保留，不称独立胜率。','', '|日期|情景|F G|F C|F N|H G|H C|H N|ΔG|ΔC|ΔN|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
  for r in rows:
   f,h=r['F'],r['H'];values=[f['G_fixed_path_addback_USD'],f['C_explicit_fees_USD'],f['N_USD'],h['G_fixed_path_addback_USD'],h['C_explicit_fees_USD'],h['N_USD'],r['delta_G_USD'],r['delta_C_USD'],r['delta_N_USD']]
   lines.append('|'+r['day']+'|'+r['model']+str(r['delay_ms'])+'|'+'|'.join(format(D(x),'.4f') for x in values)+'|')
  lines += ['', '桥恒等式：每条G−C=N、每格ΔG−ΔC=ΔN，精确残差均为0。16条result/summary现金与费用逐项匹配独立全账终端见证；maker_notional×0.003＋taker_notional×0.004逐项精确等于C，分项保存于bridge.json。没有重扫大账或读取原行情。','', '加回费用只是同一保存成交路径的会计操作，不会重建真实零费率下的资金预留、可报价、成交、库存或退出，不能称零费率策略收益。G仍含价格/库存、终端深度与1bp滑点影响，不是纯做市价差或预测alpha。风险和分项归因保持原UNKNOWN，毛净额算术不会使其可比。','', 'G正、N负只说明该已保存路径的毛现金变化被显式费用抵消；G负说明机械加回这些费用后仍负。ΔG是完整F政策相对H的固定路径增量，混合时机/库存/成交构成，不能单独认证成交流信号因果优势。固定路径费用预算G不承诺某真实费率可使策略盈利，G≤0时任何非负显式总费均不能使这一保存路径净额转正。','', '本轮仅一次JSON标量分析：16条N/C和8格会计桥，没有导入引擎/reader、重放/模型/调参/费率扫描、新数据/网络/下载/安装/付费/账户钱包/交易，旧实验与STOP不动。来源身份、helper SHA、命令/PID/资源与完整回执见started/completion-receipt及bridge.json。actual model/effort/speed UNKNOWN；规则PERMISSIONS-2026-10-14-v1、ROUTING-2026-10-13-v4、HANDOFF-2026-10-10-v2。']
  with (OUT/'README.md').open('x') as f:f.write('\n'.join(lines)+'\n')
  guard();status='COMPLETE'
  print(json.dumps({'status':status,'paths':16,'comparisons':8,'rows':[{'day':r['day'],'scenario':r['model']+str(r['delay_ms']),'F_G':r['F']['G_fixed_path_addback_USD'],'F_C':r['F']['C_explicit_fees_USD'],'F_N':r['F']['N_USD'],'deltaG':r['delta_G_USD'],'deltaC':r['delta_C_USD'],'deltaN':r['delta_N_USD']} for r in rows]}),flush=True)
 except BaseException as exc:
  if not (OUT/'first-stop.json').exists():save('first-stop.json',{'utc':utc(),'error_type':type(exc).__name__,'message':str(exc),'no_retry':True})
  raise
 finally:
  signal.setitimer(signal.ITIMER_REAL,0)
  save('completion-receipt.json',{'utc':utc(),'status':status,'exit_code':0 if status=='COMPLETE' else 1,'pid':os.getpid(),'script_sha256':sha(__file__),'CPU_seconds':time.process_time(),'wall_seconds':time.monotonic()-BOOT,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'threads':1,'network':0,'output_bytes_before_receipt':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'sources':sources,'output_sha256':{n:sha(OUT/n) for n in ('bridge.json','README.md') if (OUT/n).exists()},'actual_model':'UNKNOWN','actual_effort':'UNKNOWN'})
if __name__=='__main__':main()
