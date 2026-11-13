"""Only entry point: synthetic/preflight separate, one released formal process."""
import sys
from analysis import *

def source_seal():
 return {name:sha(OWNER/name) for name in ('core.py','analysis.py','run.py','tests.py','parameters.json')}

def execute_preflight(budget):
 if sha(PLAN)!=PLAN_SHA:raise RuntimeError('Plan changed')
 inputs=[inspect_cache(x,budget) for x in cache_inputs()]
 return {'status':'PREPARATION_READY_NO_NEW_MARKET_GET_NO_FORMAL_LABELS','utc':now(),'inputs':inputs,'plan_sha256':PLAN_SHA,'sources':source_seal(),'Python':sys.version,'raw_GETs':0,'formal_labels':0}

def execute_formal(budget):
 release=json.loads((ROOT/'root/formal-release.json').read_text());sealpath=OWNER/'preparation-seal.json';seal=json.loads(sealpath.read_text())
 if release.get('status')!='RELEASED_ONE_TWO_DAY_UNIT' or release.get('preparation_seal_sha256')!=sha(sealpath):raise RuntimeError('Root release identity missing')
 if sha(PLAN)!=PLAN_SHA or source_seal()!=seal['sources']:raise RuntimeError('Frozen plan/source/parameters changed')
 if sha(OWNER/'preflight.json')!=seal['preflight_sha256']:raise RuntimeError('Preflight changed')
 current=cache_inputs();frozen=seal['inputs']
 if len(current)!=2 or len(frozen)!=2:raise RuntimeError('Frozen cache count mismatch')
 for now_item,item,day in zip(current,frozen,DATES):
  if any(now_item[k]!=item[k] for k in ('date','path','sha256','rows')) or item['date']!=day or item['actual_sha256']!=item['sha256']:raise RuntimeError('Frozen cache identity drift')
  if sha(item['path'])!=item['sha256']:raise RuntimeError('Actual cache differs from frozen identity')
 data=acquire_all(budget)
 print(json.dumps({'event':'data_sealed','utc':now(),'GETs':budget.gets,'download_bytes':budget.bytes}),flush=True)
 days=[]
 for item,ds in zip(frozen,data):
  if sha(ds['normalized_path'])!=ds['normalized_sha256']:raise RuntimeError('Sealed trade identity drift')
  result=analyze_day(item,ds,budget);days.append(result)
  if not result['label_coverage_pass_80pct'] or not result.get('minimum100_independent_passive_IDs_each_policy_direction',False):
   terminal={'status':'INPUT_INDETERMINATE_STOP','utc':now(),'day':item['date'],'reason':'label coverage or policy-direction independent ID denominator','completed_days':days,'no_replacement':True}
   write_new(OWNER/'result.json',terminal);write_new(OWNER/'first-stop.json',terminal);return terminal
 uncertainty=bootstrap(days,budget)
 d=.5*(days[0]['D_day']+days[1]['D_day'])
 if not uncertainty['minimum1900_pass']:status='INDETERMINATE_BOOTSTRAP_STOP'
 elif any(x['D_day']<=0 for x in days) or uncertainty['CI_type7_2.5_97.5'][0]<=0:status='FIXED_CANDIDATE_NOT_SUPPORTED'
 else:status='HISTORICAL_MECHANISM_CANDIDATE_ONLY'
 positives=sum(x['auxiliary_all_reference_qualified_trade_counts'].get('main_positive',0) for x in days)
 result={'status':status,'utc':now(),'D':d,'daily_D':[x['D_day'] for x in days],'bootstrap':uncertainty,
         'auxiliary_status':'NO_POSITIVE_QUALIFIED_SPACE_FIXED_1S_EXIT' if positives==0 else 'SOME_POSITIVE_IDEAL_SPACE_NOT_EXECUTABLE_PROFIT',
         'auxiliary_main_positive_reports':positives,'statistic_not_gated_by_costs':True,'no_personal_profit_or_capacity_claim':True,'summary_files':[str(OWNER/f'{d}-summary.json') for d in DATES]}
 write_new(OWNER/'result.json',result)
 if status!='HISTORICAL_MECHANISM_CANDIDATE_ONLY':write_new(OWNER/'first-stop.json',result)
 return result

def main():
 phase=sys.argv[1]
 if phase not in ('preflight','formal'):raise RuntimeError('Unknown phase')
 if (OWNER/'first-stop.json').exists():raise RuntimeError('Existing first STOP preserved; no continuation')
 if phase=='formal' and (OWNER/'first-started.json').exists():raise RuntimeError('Single formal start already exists; never restart')
 budget=None
 try:
  if phase=='formal':write_new(OWNER/'first-started.json',{'utc':now(),'pid':os.getpid(),'sources':source_seal(),'phase':'one formal acquire-QC-seal-analysis'})
  budget=Budget(phase)
  result=execute_preflight(budget) if phase=='preflight' else execute_formal(budget)
  if phase=='preflight':write_new(OWNER/'preflight.json',result)
  rec=budget.finish(result['status']);print(json.dumps({'status':result['status'],'resource':rec}),flush=True)
 except BaseException as exc:
  signal.setitimer(signal.ITIMER_REAL,0)
  err={'status':'TERMINAL_FORMAL_FAILURE_NO_RERUN' if phase=='formal' else 'PREFLIGHT_FAILURE','utc':now(),'type':type(exc).__name__,'message':str(exc)}
  if phase=='formal' and not (OWNER/'first-stop.json').exists():write_new(OWNER/'first-stop.json',err)
  elif phase=='preflight':write_new(OWNER/f'preflight-error-{time.time_ns()}.json',err)
  if budget is not None:
   try:budget.finish(err['status'])
   except BaseException:pass
  raise
if __name__=='__main__':main()
