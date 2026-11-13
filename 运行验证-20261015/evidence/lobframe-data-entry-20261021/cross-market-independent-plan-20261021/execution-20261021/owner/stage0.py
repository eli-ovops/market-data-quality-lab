"""Independent stdlib-only Stage0. No network/model imports or account operations."""
import os, time
PROCESS_START=time.monotonic()
# Numerical libraries are not used; enforce limits also for any accidental child.
for _key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
import csv, gzip, hashlib, json, math, resource, signal, sys, time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext, ROUND_CEILING
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT.parent.parent
OWNER = ROOT/'owner'
OUT = ROOT/'stage0'
DATES = ('2026-07-01','2026-08-01','2026-09-01')
PLAN_SHA = 'd1621c849ce25d66c81e8121c46186e78eaabb759d3a75ca347ae6937c595d50'
ORIGIN = datetime(2026,10,21,11,26,52,tzinfo=timezone.utc).timestamp()
MEM_CAP=2147483648
DISK_CAP=536870912
COMPUTE_CAP=3600
D=Decimal
NOMINAL=D('4000'); FEE=D('.004'); BUY_SLIP=D('1.0001'); SELL_SLIP=D('.9999')
START_US=60_000_000; END_US=86_398_000_000; STEP_US=2_000_000


def utc(): return datetime.now(timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    return h.hexdigest()
def write_new(path,obj):
    with Path(path).open('x') as f: json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def disk_bytes():
    size=0
    for p in ROOT.rglob('*'):
        if p.is_symlink(): raise RuntimeError('Unexpected output symlink')
        if p.is_file(): size+=p.stat().st_size
    return size

def old_compute():
    total=0
    for p in OWNER.glob('resource-*.json'):
        total+=json.loads(p.read_text())['wall_seconds']
    return total

class Budget:
    def __init__(self,phase):
        self.phase=phase;self.start=PROCESS_START;self.cpu=0.0;self.prior=old_compute()
        if self.prior>=COMPUTE_CAP: raise RuntimeError('Compute budget exhausted')
        remain=min(COMPUTE_CAP-self.prior,ORIGIN+14400-time.time())
        if remain<=0: raise RuntimeError('Active deadline exhausted')
        signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Wall/active budget exceeded')))
        signal.setitimer(signal.ITIMER_REAL,remain)
        # CPU hard guard supplements frequent RSS/disk/wall checks.
        resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(COMPUTE_CAP-self.prior),math.ceil(COMPUTE_CAP-self.prior)+1))
        self.check()
    def check(self):
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>MEM_CAP: raise RuntimeError('RSS cap exceeded')
        if disk_bytes()>DISK_CAP: raise RuntimeError('New unit disk cap exceeded')
        if self.prior+time.monotonic()-self.start>COMPUTE_CAP: raise RuntimeError('Compute wall cap exceeded')
        if time.time()>ORIGIN+14400: raise RuntimeError('Active deadline exceeded')
    def finish(self,status):
        signal.setitimer(signal.ITIMER_REAL,0)
        self.check()
        rec={'phase':self.phase,'utc':utc(),'pid':os.getpid(),'status':status,
             'wall_seconds':time.monotonic()-self.start,'process_cpu_seconds':time.process_time()-self.cpu,
             'previous_compute_wall_seconds':self.prior,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'disk_bytes':disk_bytes(),'threads_used':1,'actual_model':'UNKNOWN','actual_effort':'UNKNOWN',
             'download_bytes':0,'payment_USD':0,'installs':0,'unit_origin_utc':'2026-10-21T11:26:52Z'}
        rec['cumulative_compute_wall_seconds']=rec['previous_compute_wall_seconds']+rec['wall_seconds']
        write_new(OWNER/f'resource-{self.phase}-{time.time_ns()}.json',rec)
        return rec


def safe_inputs():
    receipt=BASE/'execution-20261021/data-receipt.json'
    original=json.loads(receipt.read_text())
    chosen=[]
    allowed=(BASE/'execution-20261021/data').resolve(strict=True)
    for day in DATES:
        item=[x for x in original['files'] if x['date']==day]
        if len(item)!=1: raise RuntimeError('Input date not unique')
        r=item[0]; p=Path(r['path'])
        # Inspect components only of the three explicitly authorized project paths.
        if not p.is_absolute() or not p.is_relative_to(allowed): raise RuntimeError('Input outside project cache')
        q=p
        while q!=BASE:
            if q.is_symlink(): raise RuntimeError('Input path contains symlink')
            q=q.parent
        resolved=p.resolve(strict=True)
        if resolved!=p or not resolved.is_relative_to(allowed): raise RuntimeError('Input identity resolves elsewhere')
        if p.name!=f'bitstamp_BTCUSD_book_snapshot_25_{day}.csv.gz': raise RuntimeError('Input filename mismatch')
        chosen.append({'date':day,'path':str(p),'expected_sha256':r['compressed_sha256'],'expected_rows':r['rows']})
    return chosen


def day_start(day): return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())*1_000_000

def required_header():
    return ['exchange','symbol','timestamp','local_timestamp']+[f'{side}[{k}].{field}' for k in range(25) for side in ('asks','bids') for field in ('price','amount')]

@dataclass
class State:
    ts:int
    row:int
    batch_first_row:int
    values:tuple


def groups(path,day,meta,budget=None,identity_only=False):
    """Consume every CSV row through gzip EOF; yield only each equal-ts batch's last row."""
    start=day_start(day); stop=start+86_400_000_000
    meta.update(rows=0,batches=0,same_timestamp_rows=0,gzip_crc_verified=False)
    previous=None; prev_exchange=None; current=None
    with gzip.open(path,'rt',newline='') as f:
        reader=csv.reader(f);header=next(reader)
        if len(header)!=len(set(header)): raise RuntimeError('Duplicate schema field')
        if set(header)!=set(required_header()): raise RuntimeError('Unexpected 25-level schema')
        ix={key:header.index(key) for key in required_header()}
        keys=required_header()[4:]
        meta['header']=header
        for rownum,row in enumerate(reader,1):
            if len(row)!=len(header): raise RuntimeError('CSV width mismatch')
            if row[ix['exchange']]!='bitstamp' or row[ix['symbol']]!='BTCUSD': raise RuntimeError('Wrong exchange/symbol')
            ts=int(row[ix['local_timestamp']]);ex=int(row[ix['timestamp']])
            if not start<=ts<stop or not start<=ex<stop: raise RuntimeError('Timestamp outside fixed day')
            if previous is not None and (ts<previous or ex<prev_exchange): raise RuntimeError('Backwards timestamp')
            meta['rows']=rownum
            if rownum==1: meta['first_local_timestamp']=ts;meta['first_exchange_timestamp']=ex
            meta['last_local_timestamp']=ts;meta['last_exchange_timestamp']=ex
            if current is not None and ts!=current.ts:
                meta['batches']+=1
                yield current
                current=None
            if current is None: first=rownum
            else: first=current.batch_first_row;meta['same_timestamp_rows']+=1
            vals=() if identity_only else tuple(row[ix[k]] for k in keys)
            current=State(ts,rownum,first,vals)
            previous=ts;prev_exchange=ex
            if budget and rownum%4000==0: budget.check()
        if current:
            meta['batches']+=1
            yield current
    meta['gzip_crc_verified']=True


def levels(state):
    try:
        x=tuple(D(s) for s in state.values)
        if len(x)!=100 or any(not y.is_finite() or y<=0 for y in x): return None
        asks=[(x[k],x[k+1]) for k in range(0,100,4)]
        bids=[(x[k+2],x[k+3]) for k in range(0,100,4)]
        if asks[0][0]<bids[0][0]: return None
        if any(asks[k][0]>asks[k+1][0] or bids[k][0]<bids[k+1][0] for k in range(24)): return None
        return asks,bids
    except Exception: return None


def ceil_fee(nominal): return (nominal*FEE).quantize(D('.01'),rounding=ROUND_CEILING)

def decimal_text(value):
    with localcontext() as c:
        c.prec=48
        return str(D(value.numerator)/D(value.denominator))


def exact_fee(value):
    cents=value*Fraction(FEE)*100
    return Fraction(-(-cents.numerator//cents.denominator),100)


def cash_flow(asks,bids,nominal=NOMINAL,buy_slip=BUY_SLIP,sell_slip=SELL_SLIP):
    """Exact rational cash/depth/sign and cent ceiling; Decimal48 only for display."""
    nominal=Fraction(nominal);left=nominal;qty=Fraction(0);buy_used=0
    for price,amount in asks:
        adjusted=Fraction(price)*Fraction(buy_slip);capacity=adjusted*Fraction(amount)
        used=min(left,capacity);qty+=used/adjusted;left-=used;buy_used+=1
        if left==0:break
    if left>0:return {'unknown':'entry_depth_insufficient'}
    left_qty=qty;sale=Fraction(0);sell_used=0
    for price,amount in bids:
        used=min(left_qty,Fraction(amount));sale+=used*Fraction(price)*Fraction(sell_slip);left_qty-=used;sell_used+=1
        if left_qty==0:break
    if left_qty>0:return {'unknown':'exit_depth_insufficient'}
    in_fee=exact_fee(nominal);out_fee=exact_fee(sale);net=sale-out_fee-nominal-in_fee
    return {'quantity_btc':decimal_text(qty),'sale_nominal':decimal_text(sale),
            'entry_fee':decimal_text(in_fee),'exit_fee':decimal_text(out_fee),
            'net_usd':decimal_text(net),'label_bp':decimal_text(net/nominal*10000),
            'exact_net_sign':1 if net>0 else -1 if net<0 else 0,
            'entry_levels_used':buy_used,'exit_levels_used':sell_used}


def ref(state,target):
    if state is None: return {'target_us':target,'unknown':'missing_state'}
    out={'target_us':target,'local_timestamp':state.ts,'data_row':state.row,'batch_first_row':state.batch_first_row,
         'batch_last_row':state.row,'age_us':target-state.ts}
    if not 0<=target-state.ts<=1_000_000: out['unknown']='state_age_exceeded'
    return out


def score_pair(a,b,u,v):
    ra=ref(a,u);rb=ref(b,v)
    reasons=[]
    for tag,r in (('entry',ra),('exit',rb)):
        if 'unknown' in r: reasons.append(tag+'_'+r['unknown'])
    la=None if a is None else levels(a);lb=None if b is None else levels(b)
    if a is not None and la is None: reasons.append('entry_invalid_25_levels')
    if b is not None and lb is None: reasons.append('exit_invalid_25_levels')
    if reasons:return {'entry':ra,'exit':rb,'unknown_reasons':reasons}
    value=cash_flow(la[0],lb[1])
    if 'unknown' in value:return {'entry':ra,'exit':rb,'unknown_reasons':[value['unknown']]}
    return {'entry':ra,'exit':rb,**value}


def quantile(values,q):
    if not values:return None
    with localcontext() as c:
        c.prec=48
        pos=D(len(values)-1)*q;j=int(pos);f=pos-j
        return str(values[j]*(1-f)+values[min(j+1,len(values)-1)]*f)


def screen_day(item,budget):
    meta={};it=iter(groups(item['path'],item['date'],meta,budget));nxt=next(it,None);last=None
    def at(target):
        nonlocal nxt,last
        while nxt is not None and nxt.ts<=target:
            last=nxt;nxt=next(it,None)
        return last
    counts=Counter();reason_counts=Counter();overlap=Counter();nets=[];witness={};start=day_start(item['date'])
    out=OUT/f"{item['date']}-endpoint-records.jsonl.gz"
    with gzip.open(out,'xt',encoding='utf-8') as f:
        for offset in range(START_US,END_US,STEP_US):
            t=start+offset;u=t+500_000;v=t+1_000_000
            a=at(u);b=at(v);r={'decision_us':t,**score_pair(a,b,u,v)};counts['grid_total']+=1
            if 'unknown_reasons' in r:
                counts['unknown']+=1
                for why in r['unknown_reasons']:reason_counts[why]+=1
                overlap[' & '.join(sorted(r['unknown_reasons']))]+=1
            else:
                counts['valid']+=1;net=D(r['net_usd']);nets.append(net)
                kind='positive' if r['exact_net_sign']>0 else 'negative' if r['exact_net_sign']<0 else 'zero';counts[kind]+=1
                if 'first_valid' not in witness:witness['first_valid']=r
                if 'minimum' not in witness or net<D(witness['minimum']['net_usd']):witness['minimum']=r
                if 'maximum' not in witness or net>D(witness['maximum']['net_usd']):witness['maximum']=r
            if counts['grid_total'] in (1,10000,20000,30000,40000):witness[f"fixed_grid_{counts['grid_total']}"]=r
            f.write(json.dumps(r,separators=(',',':'))+'\n')
            if counts['grid_total']%2000==0:budget.check()
    # Exhaust tail through gzip EOF/CRC even if decision range ended earlier.
    for _ in it:pass
    if meta['rows']!=item['expected_rows']:raise RuntimeError('Rows differ from original receipt')
    nets.sort()
    summary={'date':item['date'],'counts':{k:counts[k] for k in ('grid_total','valid','unknown','positive','zero','negative')},
             'unknown_reason_counts_overlapping':dict(reason_counts),'unknown_reason_joint_counts':dict(overlap),
             'net_usd_quantiles':{str(q):quantile(nets,D(q)) for q in ('0','.01','.25','.5','.75','.99','1')},
             'quantile_definition':'linear type7 over valid net USD, sorted ascending; no unknown imputation',
             'witnesses':witness,'input_metadata':meta,'endpoint_records_path':str(out),'endpoint_records_sha256':sha(out)}
    write_new(OUT/f"{item['date']}-summary.json",summary)
    return summary


def preflight(budget):
    if (OUT/'formal-started.json').exists():raise RuntimeError('Formal stage already started')
    items=safe_inputs();results=[]
    for item in items:
        actual=sha(item['path'])
        if actual!=item['expected_sha256']:raise RuntimeError('Compressed input hash mismatch')
        meta={}
        for _ in groups(item['path'],item['date'],meta,budget,identity_only=True):pass
        if meta['rows']!=item['expected_rows']:raise RuntimeError('Input row identity mismatch')
        results.append({**item,'actual_sha256':actual,'identity_qc':meta})
    return {'status':'PRECHECK_PASS_NO_ECONOMIC_RESULTS','utc':utc(),'inputs':results,
            'implementation_sha256':sha(__file__),'proposal_sha256':PLAN_SHA,'threads_used':1,
            'method':'stream compressed SHA then complete gzip/CSV identity/UTC/monotonic and batch checks; no quote economics',
            'memory_design':'one CSV record/batch at a time; formal at most 43169 Decimal scalars/day, no dense market arrays',
            'formal_output_estimate_bytes':60_000_000,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def bind_frozen_inputs(current,sealed):
    """Use only this unit's frozen identity, rejecting mutable-receipt drift."""
    keys=('date','path','expected_rows','expected_sha256')
    if len(current)!=len(DATES) or len(sealed)!=len(DATES):
        raise RuntimeError('Frozen input count mismatch')
    bound=[]
    for day,now,frozen in zip(DATES,current,sealed):
        if frozen.get('date')!=day or now.get('date')!=day:
            raise RuntimeError('Frozen input date/order mismatch')
        if any(now.get(k)!=frozen.get(k) for k in keys):
            raise RuntimeError('Mutable receipt differs from frozen input identity')
        if frozen.get('actual_sha256')!=frozen.get('expected_sha256'):
            raise RuntimeError('Frozen actual/expected input hash mismatch')
        bound.append({k:frozen[k] for k in keys})
    return bound


def formal(budget):
    gate=ROOT/'root/formal-release.json'
    if not gate.exists():raise RuntimeError('No root formal release')
    release=json.loads(gate.read_text())
    seal=json.loads((OWNER/'preflight-seal.json').read_text())
    if release.get('status')!='RELEASED_FOR_ONE_STAGE0_FORMAL' or release.get('preflight_seal_sha256')!=sha(OWNER/'preflight-seal.json'):
        raise RuntimeError('Release identity mismatch')
    if sha(__file__)!=seal['implementation_sha256']:raise RuntimeError('Implementation drift')
    if sha(OWNER/'test-stage0.py')!=seal['tests_sha256']:raise RuntimeError('Test drift')
    if sha(OWNER/'preflight.json')!=seal['preflight_sha256']:raise RuntimeError('Preflight drift')
    items=bind_frozen_inputs(safe_inputs(),seal['inputs'])
    for item in items:
        if sha(item['path'])!=item['expected_sha256']:raise RuntimeError('Formal input SHA mismatch')
    write_new(OUT/'formal-started.json',{'utc':utc(),'pid':os.getpid(),'implementation_sha256':sha(__file__),
               'preflight_seal_sha256':sha(OWNER/'preflight-seal.json')})
    summaries=[]
    for item in items:
        summaries.append(screen_day(item,budget))
        print(json.dumps({'event':'day_complete','date':item['date'],'utc':utc()}),flush=True)
    totals=Counter()
    for s in summaries:totals.update(s['counts'])
    status='STOP_ZERO_VALID' if totals['valid']==0 else 'STOP_NO_POSITIVE_VALID_SPACE' if totals['positive']==0 else 'STAGE0_SPACE_PRESENT_PENDING_ROOT'
    result={'status':status,'utc':utc(),'totals':dict(totals),'daily_summary_paths':[str(OUT/f"{x['date']}-summary.json") for x in items],
            'interpretation':'Only fixed target-grid ideal necessary space at specified costs; no causal prediction/strategy/profit/capacity proof',
            'unknowns_not_negative':True,'no_Kraken_model_or_future_access':True}
    write_new(OUT/'result.json',result)
    if status.startswith('STOP_'):write_new(OUT/'terminal-stop.json',result)
    return result


def main():
    OWNER.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
    phase=sys.argv[1]
    if phase not in ('preflight','formal'):raise RuntimeError('Unknown phase')
    if (OUT/'terminal-stop.json').exists():raise RuntimeError('Existing terminal STOP preserved; refusing')
    if phase=='formal' and (OUT/'formal-started.json').exists():raise RuntimeError('Formal single-use marker exists; no restart')
    budget=None
    try:
        budget=Budget(phase)
        plan=ROOT.parent/'跨市场信息-一次独立挑战最小方案-20261021.md'
        if sha(plan)!=PLAN_SHA:raise RuntimeError('Frozen proposal identity mismatch')
        result=preflight(budget) if phase=='preflight' else formal(budget)
        if phase=='preflight':write_new(OWNER/'preflight.json',result)
        rec=budget.finish(result['status'])
        print(json.dumps({'status':result['status'],'resource':rec}),flush=True)
    except BaseException as exc:
        signal.setitimer(signal.ITIMER_REAL,0)
        if phase=='formal':
            if not (OUT/'terminal-stop.json').exists():write_new(OUT/'terminal-stop.json',{'status':'TERMINAL_FORMAL_FAILURE','utc':utc(),'type':type(exc).__name__,'message':str(exc)})
        else:write_new(OWNER/f'preflight-error-{time.time_ns()}.json',{'utc':utc(),'type':type(exc).__name__,'message':str(exc)})
        if budget is not None:
            try:budget.finish('ERROR')
            except BaseException:pass
        raise

if __name__=='__main__':main()
