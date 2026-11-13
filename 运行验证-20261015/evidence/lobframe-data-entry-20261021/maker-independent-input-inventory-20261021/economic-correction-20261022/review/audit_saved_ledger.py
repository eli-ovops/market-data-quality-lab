"""Independent saved-ledger accounting only; never imports replay or reads market sources."""
import csv,gzip,json,pathlib,time,resource,signal,hashlib,os,sys
from decimal import Decimal as D,getcontext
getcontext().prec=60
HERE=pathlib.Path(__file__).resolve().parent
OWNER=HERE.parent/'owner'
START=time.process_time();WALL=time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU,(35,36))
def guard(*unused):
    if time.process_time()-START>34:raise TimeoutError('review CPU ceiling')
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>134217728:raise MemoryError('review RSS ceiling')
signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,1,1)
out={'scope':'All saved ledger rows; accounting only, no event/queue/risk replay','days':[]}
for day in ('2026-05-01','2026-06-01'):
    summary=json.loads((OWNER/(day+'-summary.json')).read_text())
    states={};counts={};first={};last={};terms=[];unknowns={};filldigest=hashlib.sha256();n=0
    path=OWNER/(day+'-ledger.csv.gz')
    with gzip.open(path,'rt',newline='') as f:
        reader=csv.DictReader(f);header=reader.fieldnames
        for n,r in enumerate(reader,1):
            k=(r['policy'],r['model'],r['delay_ms']);prev=states.get(k,('5000','0','0'))
            current=(r['cash'],r['BTC'],r['fees'])
            if r['event']=='fill':
                x=json.loads(r['detail']);q=D(x['qty']);p=D(x['fill_price']);fee=D(x['fee']);rate=D(x['fee_rate'])
                assert q>0 and p>0 and fee==q*p*rate
                assert rate==(D('.004') if x['fill_kind']=='terminal' else D('.003'))
                dq=q if r['side']=='buy' else -q
                assert D(current[0])==D(prev[0])-dq*p-fee,(day,n,'cash')
                assert D(current[1])==D(prev[1])+dq,(day,n,'BTC')
                assert D(current[2])==D(prev[2])+fee,(day,n,'fee')
                assert D(current[0])>=0 and D(current[1])>=0
                counts[k]=counts.get(k,0)+1
                witness={a:r[a] for a in ('t','policy','model','delay_ms','side','cash','BTC','fees','detail')}
                first.setdefault(k,witness);last[k]=witness
                filldigest.update(json.dumps(witness,sort_keys=True).encode())
            else:
                assert current==prev or all(D(a)==D(b) for a,b in zip(current,prev)),(day,n,'nonfill balance change')
            if r['event']=='terminal_complete':
                assert D(r['BTC'])==0 and D(r['reserved_cash'])==D(r['reserved_BTC'])==D(r['pending_buy_BTC'])==0
                terms.append({a:r[a] for a in ('t','policy','model','delay_ms','cash','BTC','fees','detail')})
            if r['event'].startswith('UNKNOWN'):unknowns[r['event']]=unknowns.get(r['event'],0)+1
            states[k]=current
    assert n==summary['ledger_rows']
    assert len(states)==len(terms)==len(summary['results'])==8
    for r in summary['results']:
        k=(r['policy'],r['model'],str(r['delay_ms']));s=states[k]
        assert all(D(a)==D(b) for a,b in zip(s,(r['cash'],r['BTC'],r['fees_USD'])))
        assert counts.get(k,0)==r['counts'].get('fills',0)
        assert D(s[0])-5000==D(r['PnL_USD'])
        complete=not r['unknown'] and len([z for z in terms if (z['policy'],z['model'],z['delay_ms'])==k])==1
        assert (r['execution_cash_status']=='COMPLETE_CONDITIONAL_MODEL_CASH')==complete
        assert (r['risk_status']=='COMPLETE_MODEL_RISK')==(r['risk_unknown_count']==0)
        assert (r['status']=='MODEL_PATH_COMPLETE')==(complete and r['risk_unknown_count']==0)
    out['days'].append({'day':day,'header':header,'all_rows_checked':n,'all_paths_checked':8,'fill_rows_checked':sum(counts.values()),'fills_by_path':{'|'.join(k):v for k,v in counts.items()},'all_fill_witness_digest':filldigest.hexdigest(),'first_fill_each_path':list(first.values()),'last_fill_each_path':list(last.values()),'all_terminal_complete_witnesses':terms,'UNKNOWN_event_counts':unknowns,'all_summary_balances_matched':True})
result=json.loads((OWNER/'result.json').read_text())
assert len(result['path_results'])==16 and len(result['comparisons'])==8
allpaths=[]
for day in ('2026-05-01','2026-06-01'):
    allpaths.extend(json.loads((OWNER/(day+'-summary.json')).read_text())['results'])
assert result['path_results']==allpaths
for x in result['comparisons']:
    f=next(r for r in allpaths if r['day']==x['day'] and r['model']==x['model'] and r['delay_ms']==x['delay_ms'] and r['policy']=='F')
    h=next(r for r in allpaths if r['day']==x['day'] and r['model']==x['model'] and r['delay_ms']==x['delay_ms'] and r['policy']=='H')
    fk=f['execution_cash_status']=='COMPLETE_CONDITIONAL_MODEL_CASH';hk=h['execution_cash_status']=='COMPLETE_CONDITIONAL_MODEL_CASH'
    assert x['F_cash_complete']==fk and x['H_cash_complete']==hk and x['complete_cash_comparison']==(fk and hk)
    assert x['F_PnL_USD']==f['PnL_USD'] and x['H_PnL_USD']==h['PnL_USD']
    delta=D(f['PnL_USD'])-D(h['PnL_USD']) if fk and hk else None
    assert (delta is None and x['delta_F_minus_H_USD'] is None) or (delta is not None and delta==D(x['delta_F_minus_H_USD']))
    rk=f['risk_status']==h['risk_status']=='COMPLETE_MODEL_RISK'
    assert x['risk_complete_both']==rk
    keys=('max_inventory_notional_USD','inventory_BTC_seconds','max_drawdown_USD')
    assert x['F_risk_metrics']=={k:f[k] for k in keys} and x['H_risk_metrics']=={k:h[k] for k in keys}
    if not rk:assert x['risk_comparable_and_F_not_higher'] is None
    else:assert x['risk_comparable_and_F_not_higher']==all(D(f[k])<=D(h[k]) for k in keys)
    cashfail=(fk and D(f['PnL_USD'])<=0) or (fk and hk and delta<=0)
    if cashfail:assert x['status']=='CASH_NECESSARY_CONDITION_NOT_PASSED'
    if not(fk and hk) and not cashfail:assert x['status']=='UNKNOWN_EXECUTION_CASH_SUBPATH'
    if fk and hk and not cashfail and not rk:assert x['status']=='CASH_PASS_RISK_UNKNOWN_NOT_PROMOTED'
    if x['status']=='MODEL_CONDITIONAL_CELL_PASS':assert fk and hk and not cashfail and rk and x['risk_comparable_and_F_not_higher'] is True
assert (result['status']=='FIXED_COMBINATION_CASH_NECESSARY_CONDITIONS_NOT_PASSED')==any(x['status']=='CASH_NECESSARY_CONDITION_NOT_PASSED' for x in result['comparisons'])
assert result['has_execution_cash_unknown']==any(not x['complete_cash_comparison'] for x in result['comparisons'])
assert result['has_risk_unknown']==any(not x['risk_complete_both'] for x in result['comparisons'])
signal.setitimer(signal.ITIMER_REAL,0)
out.update(status='PASS_SAVED_ACCOUNTING_AND_REPORTED_STATE_CONSISTENCY',result_comparisons_checked=8,result_paths_checked=16,pid=os.getpid(),executable=sys.executable,reported_exit_code=0,CPU_seconds=time.process_time()-START,wall_seconds=time.monotonic()-WALL,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
with (HERE/'saved-ledger-audit.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='days'}));print([(x['day'],x['all_rows_checked'],x['fill_rows_checked']) for x in out['days']])
