"""Fixed historical quote arithmetic only; no model, signal or account simulation."""
import csv,gzip,hashlib,json,math,time
from datetime import datetime,timezone
from decimal import Decimal,getcontext
from pathlib import Path
getcontext().prec=50
P=Path(__file__).resolve().parent
INPUT=P/'bitstamp_book_snapshot_25_2026-10-01_BTCUSD.csv.gz'
SHA='22d347447c1b12f422ea2ed16ba84725eb1b8c716a22aa6b53f775f7e2fd2fe0'
OUT=P/'quote-cost-statistics.json'
PAIRS=P/'sealed_quote_pairs.json'
BP=Decimal(10000);S=Decimal(1)/BP
DLY=(1,5);FEES=(0,5,10,25,50)
START=int(datetime(2026,10,1,0,5,tzinfo=timezone.utc).timestamp())*1000000
REQ=[f'{s}[{i}].{v}' for s in ('asks','bids') for i in range(10) for v in ('price','amount')]
T0=time.monotonic()

def margin(ask,bid,fee,slip):
    n=Decimal(bid)*(1-slip)*(1-fee)
    d=Decimal(ask)*(1+slip)*(1+fee)
    return (n/d-1)*BP,n>d

def stats(vals):
    a=sorted(vals)
    if not a:return None
    n=len(a)
    median=a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2
    return {'n':n,'min':str(a[0]),'median':str(median),'max':str(a[-1])}

def qcheck(row):
    if row['exchange']!='bitstamp' or row['symbol']!='BTCUSD':return False,'identity'
    try:
        v=[float(row[k]) for k in REQ]
        if any(not math.isfinite(x) or x<=0 for x in v):return False,'nonpositive_or_nonfinite'
        a=v[:20:2];b=v[20:40:2]
        if b[0]>=a[0]:return False,'locked_or_crossed'
        if any(a[i]>=a[i+1] or b[i]<=b[i+1] for i in range(9)):return False,'unsorted'
        return True,None
    except (ValueError,KeyError):return False,'unparseable_leg'

def main():
    if OUT.exists() or PAIRS.exists() or (P/'quote-cost-statistics-stop.json').exists():raise RuntimeError('Existing results or STOP preserved; no rerun')
    h=hashlib.sha256()
    with INPUT.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b)
    if h.hexdigest()!=SHA:raise RuntimeError('Input SHA mismatch')
    # Independent hand-solvable numerical checks, not market evidence.
    assert margin('100','100',Decimal(0),Decimal(0))==(Decimal(0),False)
    assert margin('100','101',Decimal(0),Decimal(0))==(Decimal(100),True)
    x=(Decimal(99)/Decimal(101)-1)*BP
    assert margin('100','100',Decimal('.01'),Decimal(0))==(x,False)
    assert margin('100','100',Decimal(0),Decimal('.01'))==(x,False)
    queries=[]
    for k in range(715):
        t=START+k*120000000
        for d in DLY:
            for leg,off in [('entry',0),('exit',60000000)]:
                queries.append((t+d*1000000+off,k,d,leg))
    queries.sort();qi=0;chosen={};rows=0;groups=0;last_time=None
    def consume(ts,row,prev):
        nonlocal qi,groups
        groups+=1
        valid,reason=qcheck(row)
        gap=None if prev is None else ts-prev
        while qi<len(queries) and queries[qi][0]<=ts:
            target,k,d,leg=queries[qi]
            reasons=[]
            if not valid:reasons.append(reason)
            if ts-target>1000000:reasons.append('wait_above_1s')
            if gap is None:reasons.append('no_previous_merged_record')
            elif gap>2000000:reasons.append('preceding_gap_above_2s')
            if ts//86400000000!=target//86400000000:reasons.append('cross_day')
            chosen[(k,d,leg)]={'target_collector_us':target,'observed_collector_us':ts,'wait_us':ts-target,'previous_merged_gap_us':gap,'ask':row['asks[0].price'],'bid':row['bids[0].price'],'valid':not reasons,'reasons':reasons}
            qi+=1
    prev_group=None;group_time=None;group_row=None
    with gzip.open(INPUT,'rt',encoding='utf-8',newline='') as f:
        rd=csv.DictReader(f)
        if not set(REQ+['local_timestamp','timestamp','exchange','symbol']).issubset(rd.fieldnames or []):raise RuntimeError('Required fields missing')
        for row in rd:
            rows+=1
            if rows>2000000 or (rows%1000==0 and time.monotonic()-T0>600):raise RuntimeError('Read/time limit')
            ts=int(row['local_timestamp'])
            if last_time is not None and ts<last_time:raise RuntimeError('Global collector ordering')
            last_time=ts
            if group_time is None:group_time=ts;group_row=row
            elif ts==group_time:group_row=row
            else:
                consume(group_time,group_row,prev_group)
                prev_group=group_time;group_time=ts;group_row=row
        if group_row is not None:consume(group_time,group_row,prev_group)
    # Gzip EOF reached: CRC checked by Python gzip reader.
    sealed=[];common=[];excluded=[];causes={};blocks=[0,0,0,0]
    for k in range(715):
        t=START+k*120000000
        legs={f'{d}s_{leg}':chosen.get((k,d,leg)) for d in DLY for leg in ('entry','exit')}
        bad=[]
        for key,v in legs.items():
            if v is None:bad.append(key+':missing_quote')
            else:bad.extend(key+':'+r for r in v['reasons'])
        if bad:
            excluded.append(k)
            for r in set(bad):causes[r]=causes.get(r,0)+1
        else:
            common.append(k);blocks[(t//3600000000)%24//6]+=1
        sealed.append({'slot':k,'decision_collector_us':t,'common_valid':not bad,'legs':legs,'exclusion_reasons':bad})
    by_id={r['slot']:r for r in sealed};cells=[]
    coverage=len(common)>=500 and all(x>=100 for x in blocks)
    for d in DLY:
        for fee_bp in FEES:
            fee=Decimal(fee_bp)/BP;vals=[];positive=[];bins=[0,0,0,0]
            for k in common:
                r=by_id[k];e=r['legs'][f'{d}s_entry'];x=r['legs'][f'{d}s_exit']
                g,pos=margin(e['ask'],x['bid'],fee,S)
                vals.append(g)
                if pos:positive.append(g);bins[(r['decision_collector_us']//3600000000)%24//6]+=1
            total=sum(positive,Decimal(0))
            if not coverage:judgment='UNKNOWN_INSUFFICIENT_OBSERVABLE_COVERAGE'
            elif positive:judgment='POSITIVE_QUOTE_SPACE_PRESENT_NOT_PREDICTABILITY_OR_PROFIT'
            elif len(common)==715:judgment='NO_POSITIVE_SPACE_FOR_THIS_FIXED_FULL_GRID_CELL_ONLY'
            else:judgment='NO_POSITIVE_SPACE_IN_COMMON_VALID_SLOTS_EXCLUDED_UNKNOWN'
            cells.append({'delay_seconds':d,'fee_per_side_bp':fee_bp,'additional_slippage_per_side_bp':1,'common_valid_slots':len(common),'positive_slots':len(positive),'positive_fraction_of_common':str(Decimal(len(positive))/len(common)) if common else None,'quote_space_bp':stats(vals),'positive_slots_by_utc_6h_block':bins,'max_share_of_positive_quote_space':str(max(positive)/total) if total else None,'judgment':judgment})
    report={'status':'COMPLETED_FIXED_READ_ONLY_QUOTE_ARITHMETIC_NOT_STRATEGY_BACKTEST','at_utc':datetime.now(timezone.utc).isoformat(),'input_sha256':SHA,'source':'https://datasets.tardis.dev/v1/bitstamp/book_snapshot_25/2026/10/01/BTCUSD.csv.gz','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_rows_read':rows,'merged_collector_timestamp_groups':groups,'gzip_eof_crc_checked':True,'candidate_slots':715,'common_valid_slots':len(common),'excluded_slots':len(excluded),'excluded_slot_ids':excluded,'exclusion_reason_counts_nonexclusive':causes,'common_valid_slots_by_utc_6h_block':blocks,'coverage_minimum_met':coverage,'cells':cells,'manual_arithmetic_checks_passed':4,'models':0,'strategy_signals':0,'account_simulations':0,'trades':0,'payments':0,'dollar_profit_computed':False,'limits':['Only conditional quote space; no demonstrated tradable edge','Unknown excluded slots, source feed completeness and user machine latency','No actual personal fee, fills, liquidity capacity, impact, funding, operating cost or tax certification'],'elapsed_seconds':round(time.monotonic()-T0,3)}
    with PAIRS.open('x') as f:json.dump(sealed,f,ensure_ascii=False,indent=2)
    report['sealed_quote_pairs_sha256']=hashlib.sha256(PAIRS.read_bytes()).hexdigest()
    with OUT.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:report[k] for k in ['status','source_rows_read','candidate_slots','common_valid_slots','excluded_slots','common_valid_slots_by_utc_6h_block','coverage_minimum_met','cells','elapsed_seconds']},ensure_ascii=False,indent=2))
if __name__=='__main__':
    try:main()
    except Exception as e:
        fail=P/'quote-cost-statistics-stop.json'
        if not fail.exists():
            with fail.open('x') as f:json.dump({'status':'STOP_NO_RETRY','error_type':type(e).__name__,'reason':str(e),'models':0,'trades':0},f,ensure_ascii=False,indent=2)
        raise
