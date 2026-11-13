"""Hand-computed fixtures only. No real input opens; imports own pure definitions."""
import importlib.util,sys
from pathlib import Path
p=Path(__file__).with_name('stage0.py')
spec=importlib.util.spec_from_file_location('stage0',p);s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s)
budget=s.Budget('synthetic');checks=[];runid=str(s.time.time_ns())
def check(name,condition):
    if not condition:raise AssertionError(name)
    checks.append(name)
def flow(a,b,**kw):return s.cash_flow([(s.D(x),s.D(y)) for x,y in a],[(s.D(x),s.D(y)) for x,y in b],**kw)
try:
    # 4000 / 100 = 40 BTC, sell4200, fees16+16.8, net167.2.
    r=flow([('100','100')],[('105','100')],buy_slip=s.D(1),sell_slip=s.D(1))
    check('manual_positive_and_bilateral_fee',s.D(r['net_usd'])==s.D('167.2') and r['exact_net_sign']==1)
    r=flow([('100','100')],[('100','100')],buy_slip=s.D(1),sell_slip=s.D(1))
    check('manual_negative_equal_price',s.D(r['net_usd'])==s.D('-32') and r['exact_net_sign']==-1)
    r=flow([('100','100')],[('100.80325','100')],buy_slip=s.D(1),sell_slip=s.D(1))
    check('exact_zero_cent_boundary',s.D(r['sale_nominal'])==s.D('4032.13') and s.D(r['exit_fee'])==s.D('16.13') and r['exact_net_sign']==0)
    # Two asks: spend2000 at100 +2000 at200 =>30 BTC, sell at150 =>4500 net466.
    r=flow([('100','20'),('200','10')],[('150','30')],buy_slip=s.D(1),sell_slip=s.D(1))
    check('two_level_exact_depth',s.D(r['quantity_btc'])==30 and s.D(r['net_usd'])==466 and r['entry_levels_used']==2)
    check('entry_depth_unknown',flow([('100','1')],[('100','100')])['unknown']=='entry_depth_insufficient')
    check('exit_depth_unknown',flow([('100','100')],[('100','1')])['unknown']=='exit_depth_insufficient')
    check('fee_ceiling_not_nearest',s.ceil_fee(s.D('1.001'))==s.D('.01') and s.ceil_fee(s.D('2.5'))==s.D('.01'))
    # With slippage exactly once, buy at10001 nominal4000 gives 4000/10001;
    # sell at9999 ->3999.200079992..., ceil fee16, net -32.799920007999...
    r=flow([('10000','100')],[('10000','100')])
    check('one_slippage_each_side',abs(s.D(r['net_usd'])-s.D('-32.79992000799920007999200079992000799920007999'))<s.D('1e-38'))
    base=s.day_start('2026-07-01');meta={};fixture=s.OWNER/f'synthetic-batch-{runid}.csv.gz'
    header=s.required_header()
    def row(ts,ap):
        vals=['bitstamp','BTCUSD',str(ts),str(ts)]
        for k in range(25):vals += [str(ap+k),'100',str(99-k),'100']
        return vals
    with s.gzip.open(fixture,'xt',newline='') as f:
        w=s.csv.writer(f);w.writerow(header);w.writerow(row(base+500000,100));w.writerow(row(base+500000,101));w.writerow(row(base+1000000,102))
    g=list(s.groups(fixture,'2026-07-01',meta))
    check('same_ts_complete_last_batch',len(g)==2 and g[0].row==2 and g[0].batch_first_row==1 and g[0].values[0]=='101')
    check('asof_exact_endpoint',s.ref(g[0],base+500000)['age_us']==0)
    check('age_inclusive_and_overage', 'unknown' not in s.ref(g[0],base+1500000) and s.ref(g[0],base+1500001)['unknown']=='state_age_exceeded')
    check('missing_not_negative',s.score_pair(None,g[1],base,base+1000000).get('unknown_reasons')==['entry_missing_state'])
    check('no_after_endpoint',s.ref(g[1],base+500000)['unknown']=='state_age_exceeded')
    check('gzip_crc_fixture',meta['gzip_crc_verified'] and meta['rows']==3 and meta['same_timestamp_rows']==1)
    check('fixed_grid_boundaries',len(range(s.START_US,s.END_US,s.STEP_US))==43169 and list(range(s.START_US,s.END_US,s.STEP_US))[-1]==86396000000)
    # Invalid/crossed state and out-of-day records cannot enter a valid pair.
    bad=s.State(base,1,1,tuple(['NaN']*100));check('invalid_price_not_negative',s.score_pair(bad,g[1],base,base+1000000)['unknown_reasons']==['entry_invalid_25_levels'])
    fixture2=s.OWNER/f'synthetic-day-boundary-{runid}.csv.gz'
    with s.gzip.open(fixture2,'xt',newline='') as f:
        w=s.csv.writer(f);w.writerow(header);w.writerow(row(base-1,100))
    rejected=False
    try:list(s.groups(fixture2,'2026-07-01',{}))
    except RuntimeError as exc:rejected='outside fixed day' in str(exc)
    check('day_boundary_rejected',rejected)
    check('quantile_type7_hand',s.quantile([s.D(0),s.D(10)],s.D('.25'))=='2.50')
    result={'status':'PASS','utc':s.utc(),'checks':checks,'check_count':len(checks),'implementation_sha256':s.sha(p),'tests_sha256':s.sha(__file__),'real_inputs_opened':0,'financial_real_calculations':0}
    s.write_new(s.OWNER/'synthetic-tests.json',result);rec=budget.finish('PASS');print(s.json.dumps({'tests':result,'resource':rec}),flush=True)
except BaseException:
    try:budget.finish('FAIL')
    except BaseException:pass
    raise
