"""Passive small JSON extraction only. Never import engine or read ledgers/market data."""
import json,pathlib,hashlib,time,resource,datetime,os
start=time.process_time();base=pathlib.Path(__file__).resolve().parents[2];out=pathlib.Path(__file__).resolve().parent
paths=['economic-correction-20261022/owner/core.py','economic-correction-20261022/owner/inputs.py','economic-correction-20261022/owner/run.py','economic-correction-20261022/owner/spec.json','economic-correction-20261022/owner/result.json','economic-correction-20261022/fee-signal-readonly-20261022/accounting/bridge.json','same-window-label-diagnosis-20261022/owner/result.json','next-validation-design/最小经济验证方案.md','next-validation-design/最小经济验证方案-v2-穿价压力.md']
identities={s:hashlib.sha256((base/s).read_bytes()).hexdigest() for s in paths}
r=json.loads((base/paths[4]).read_text())
keys=('day','model','delay_ms','policy','execution_cash_status','risk_status','PnL_USD','fees_USD','maker_notional','taker_notional','inventory_BTC_seconds','longest_positive_inventory_seconds','q_BTC','risk_unknown_count','counts','attribution_status')
(out/'16path-saved-scalars.json').write_text(json.dumps({'method':'copied existing scalar fields only; no ledger scan or new trade path','paths':[{k:p[k] for k in keys} for p in r['path_results']]},indent=2)+'\n')
(out/'source-identities.json').write_text(json.dumps(identities,indent=2)+'\n')
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'CPU_seconds':time.process_time()-start,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'threads':1,'network_new_data_models_replay':0,'actual_model_effort_speed':'UNKNOWN','only_small_saved_JSON_and_source_hashes':True}
(out/'scalar-extraction-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
