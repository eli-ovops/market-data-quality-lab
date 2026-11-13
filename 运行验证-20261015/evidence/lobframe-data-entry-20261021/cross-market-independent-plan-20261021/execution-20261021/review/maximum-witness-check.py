"""Reviewer-only: three SEALED maximum witnesses, no grid/reselection/strategy.
Reads only authorized Jul/Aug/Sep project caches up to each needed row+1;
retains used price/amount fields plus adjacent timestamps. No stage0 import.
"""
import time
START=time.monotonic()
import csv,gzip,json,hashlib,resource,signal
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent.parent
REVIEW=ROOT/'review'
signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('review60s cap')))
signal.alarm(60)
resource.setrlimit(resource.RLIMIT_CPU,(60,61))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def dec(x):
    with localcontext() as c:
        c.prec=80
        return str(Decimal(x.numerator)/Decimal(x.denominator))
def fee(x):
    v=x*F(4,1000)*100
    return F((v.numerator+v.denominator-1)//v.denominator,100)
seal=json.loads((ROOT/'owner/preflight-seal.json').read_text())
manifest=json.loads((ROOT/'owner/terminal-manifest.json').read_text())
hashes={x['path']:x['sha256'] for x in manifest['files']}
receipt={'scope':'Only three presealed daily maximum witnesses; no new sample or full recalculation',
         'actual_model':'UNKNOWN','actual_effort':'UNKNOWN','network':0,'threads':1,'days':[],'artifact_hashes':[]}
for day in ('2026-07-01','2026-08-01','2026-09-01'):
    summary_path=ROOT/'stage0'/f'{day}-summary.json'
    summary=json.loads(summary_path.read_text());w=summary['witnesses']['maximum']
    for p in (summary_path,ROOT/'stage0'/f'{day}-endpoint-records.jsonl.gz'):
        actual=sha(p);assert actual==hashes[str(p)]
        receipt['artifact_hashes'].append({'path':str(p),'sha256':actual})
    counts=summary['counts'];assert counts['grid_total']==counts['valid']+counts['unknown']
    assert counts['valid']==counts['positive']+counts['zero']+counts['negative']
    assert sum(summary['unknown_reason_joint_counts'].values())==counts['unknown']
    for reason,n in summary['unknown_reason_counts_overlapping'].items():
        assert n==sum(v for k,v in summary['unknown_reason_joint_counts'].items() if reason in k.split(' & '))
    item=next(x for x in seal['inputs'] if x['date']==day);p=Path(item['path'])
    allowed=ROOT.parent.parent/'execution-20261021/data'
    assert p.is_relative_to(allowed) and p.resolve()==p and not p.is_symlink()
    assert p.name==f'bitstamp_BTCUSD_book_snapshot_25_{day}.csv.gz'
    assert item['actual_sha256']==item['expected_sha256']
    selected={}
    for leg in ('entry','exit'):
        ref=w[leg]
        selected.update({n:None for n in (ref['batch_first_row']-1,ref['data_row'],ref['batch_last_row']+1) if n>=1})
    maxrow=max(selected);rows={}
    with gzip.open(p,'rt',newline='') as f:
        reader=csv.DictReader(f)
        for n,row in enumerate(reader,1):
            if n in selected:
                keep={'local_timestamp':row['local_timestamp'],'timestamp':row['timestamp']}
                for leg,side in (('entry','asks'),('exit','bids')):
                    if n==w[leg]['data_row']:
                        for k in range(w[leg+'_levels_used']):
                            for field in ('price','amount'):keep[f'{side}[{k}].{field}']=row[f'{side}[{k}].{field}']
                rows[n]=keep
            if n>=maxrow:break
    q={};raw_legs={}
    for leg,side,mult in (('entry','asks',F(10001,10000)),('exit','bids',F(9999,10000))):
        ref=w[leg];r=rows[ref['data_row']];ts=int(r['local_timestamp'])
        assert ts==ref['local_timestamp'] and ts<=ref['target_us'] and ref['target_us']-ts==ref['age_us']<=1000000
        assert ref['data_row']==ref['batch_last_row']
        before=rows.get(ref['batch_first_row']-1);after=rows.get(ref['batch_last_row']+1)
        assert before is None or int(before['local_timestamp'])<ts
        assert after is not None and int(after['local_timestamp'])>ref['target_us']
        raw_legs[leg]={'sealed_reference':ref,'minimal_original_fields':r,'previous_batch_neighbor':before,'next_batch_neighbor':after}
        kmax=w[leg+'_levels_used'];levels=[(F(r[f'{side}[{k}].price'])*mult,F(r[f'{side}[{k}].amount'])) for k in range(kmax)]
        if leg=='entry':
            spent=sum(price*amount for price,amount in levels[:-1]);assert spent<F(4000)
            last=(F(4000)-spent)/levels[-1][0];assert 0<last<=levels[-1][1]
            qty=sum(amount for _,amount in levels[:-1])+last
        else:
            used=sum(amount for _,amount in levels[:-1]);last=qty-used;assert 0<last<=levels[-1][1]
            sale=sum(price*amount for price,amount in levels[:-1])+last*levels[-1][0]
    inf=fee(F(4000));outf=fee(sale);net=sale-outf-F(4000)-inf
    computed={'quantity_btc':qty,'sale_nominal':sale,'entry_fee':inf,'exit_fee':outf,'net_usd':net,'label_bp':net/F(4000)*10000}
    diffs={}
    with localcontext() as c:
        c.prec=85
        for k,value in computed.items():
            delta=abs(Decimal(dec(value))-Decimal(w[k]));assert delta<Decimal('1e-40')
            diffs[k]=str(delta)
    assert net<0 and w['exact_net_sign']==-1
    receipt['days'].append({'date':day,'input_path':str(p),'input_sha_from_seal_not_rehashed':item['actual_sha256'],
        'counts':counts,'unknown_joint':summary['unknown_reason_joint_counts'],'decision_us':w['decision_us'],
        'raw_legs':raw_legs,'independent_closed_form':{k:dec(v) for k,v in computed.items()},
        'absolute_display_differences':diffs,'matches':True,'source_rows_traversed_until':maxrow})
receipt['result']='PASS_THREE_FIXED_MAXIMUM_WITNESSES_ONLY'
receipt['script_sha256']=sha(Path(__file__))
receipt['completed_utc']=datetime.now(timezone.utc).isoformat()
receipt['wall_seconds']=time.monotonic()-START
receipt['process_cpu_seconds']=time.process_time()
receipt['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
assert receipt['peak_rss_bytes']<2147483648
receipt['new_files']=['review/maximum-witness-check.py','review/maximum-witness-receipt.json']
receipt['no_stage0_import_or_formal_reexecution']=True
with (REVIEW/'maximum-witness-receipt.json').open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
signal.alarm(0)
print(json.dumps({'result':receipt['result'],'wall_seconds':receipt['wall_seconds'],'peak_rss_bytes':receipt['peak_rss_bytes']}))
