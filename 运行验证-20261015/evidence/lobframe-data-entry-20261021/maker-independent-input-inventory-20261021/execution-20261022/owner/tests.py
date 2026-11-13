"""Non-market synthetic checks only, no HTTP invocation or formal labels."""
import sys,io
import core as core_module
from analysis import *
budget=Budget('synthetic');passed=[];runid=str(time.time_ns());fixture=OWNER/f'synthetic-{runid}';fixture.mkdir()
def check(name,value):
 if not value:raise AssertionError(name)
 passed.append(name)
def fails(name,fn,typ=Exception):
 yes=False
 try:fn()
 except typ:yes=True
 check(name,yes)
def tr(cap,src=100,ident=1,buy=10,sell=20,typ=0,price='100'):return Trade(cap,src,ident,buy,sell,typ,price,0,1)
def bb(caps,sources,bids=None,asks=None,bad=None):
 n=len(caps);return BBO(array.array('q',caps),array.array('q',sources),array.array('I',range(1,n+1)),array.array('B',bad or [0]*n),bids or ['100']*n,asks or ['100']*n,{})
try:
 base=day0(DATES[0]);trade=tr(base+6*TICK+2500000,src=100)
 check('seven_digit_capture_exact',capture('2026-05-01T00:00:00.0000001Z')==base+1)
 fails('reject_six_digit_capture',lambda:capture('2026-05-01T00:00:00.000001Z'))
 target=trade.cap+TICK;bbo=bb([target-20],[103]);label,_=label_reference(trade,bbo)
 check('strict_interval_reference_valid',label is not None)
 check('equal_capture_interval_boundary_UNKNOWN',label_reference(trade,bb([target-11],[103]))[1]=='asof_capture_intervals_overlap')
 check('source_microsecond_uncertainty_equal_boundary_UNKNOWN',label_reference(trade,bb([target-20],[102]))[1]=='BBO_source_not_strictly_later')
 check('next_nominal_quote_overlap_UNKNOWN',label_reference(trade,bb([target-20,target+11],[103,104]))[1]=='next_BBO_capture_uncertain_at_target')
 check('worst_age_exactly1s_allowed',label_reference(trade,bb([target-TICK+11],[103]))[0] is not None)
 check('worst_age_one_tick_over_UNKNOWN',label_reference(trade,bb([target-TICK+10],[103]))[1]=='BBO_worst_age_over_1s')
 check('invalid_conflict_or_regression_UNKNOWN',label_reference(trade,bb([target-20],[103],bad=[1]))[1]=='BBO_invalid_conflict_or_source_regression')
 main,zero=auxiliary(trade,bbo,label)
 check('passive_sell_cost_hand_minus71.004bp',main==Fraction('-71.004') and zero==Fraction(-1))
 buytrade=tr(trade.cap,src=100,typ=1);main,zero=auxiliary(buytrade,bbo,label)
 check('passive_buy_cost_hand_minus70.996bp',main==Fraction('-70.996') and zero==Fraction(-1))
 check('adverse_sell_sign_hand',abs(label_reference(trade,bb([target-20],[103],['100'],['102']))[0]['loss_bp']-100)<1e-12)
 check('adverse_buy_sign_hand',abs(label_reference(buytrade,bb([target-20],[103],['100'],['102']))[0]['loss_bp']+100)<1e-12)
 seq=[tr(base+5*TICK+100,src=100),tr(base+6*TICK+100,src=101,ident=2),tr(base+6*TICK+200,src=1000,ident=3),tr(base+7*TICK+100,src=900,ident=4)]
 anchors=source_anchors(DATES[0],seq)
 check('max_source_uses_all_past_not_future',anchors[6][3]==100 and anchors[7][3]==1000)
 check('future_source_strictly_above_past_max',future_time_guard(DATES[0],seq[1],anchors)[1] is None)
 check('future_source_regression_UNKNOWN',future_time_guard(DATES[0],seq[3],anchors)[1]=='future_source_not_after_all_known_max')
 check('future_same_source_UNKNOWN',future_time_guard(DATES[0],tr(seq[1].cap,src=100),anchors)[1]=='future_source_not_after_all_known_max')
 check('future_exact_upper_grid_boundary_UNKNOWN',future_time_guard(DATES[0],tr(base+7*TICK,src=101),anchors)[1]=='future_capture_boundary_uncertain')
 check('input_boundary_overlap_UNKNOWN',ambiguous_boundary([base+6*TICK-1],base+6*TICK))
 check('input_boundary_far_enough_known',not ambiguous_boundary([base+6*TICK-2],base+6*TICK))
 check('closed_disconnect_intersection',gap_intersects(base+6*TICK,[[base+5*TICK,base+5*TICK]]))
 check('disconnect_at_excluded_upper_endpoint_no_intersection',not gap_intersects(base+6*TICK,[[base+6*TICK,base+6*TICK+1]]))
 records=[tr(base+6*TICK+10,ident=1,sell=20),tr(base+7*TICK+10,ident=2,sell=20),tr(base+8*TICK+10,ident=3,sell=30),tr(base+8*TICK+10,ident=4,sell=30)]
 chosen,tied=choose_first([0,1,2,3],records)
 check('first_order_before_score_no_later_substitution',chosen=={0} and tied=={30})
 check('fixed_domain_grid_count',len(range(5,86395))==86390)
 check('bootstrap_type7_hand',type7([0.,10.],.25)==2.5)
 # Hand direction-standardized table: z_buy=(3+9)/2=6, z_sell10, hash_buy0, hash_sell6 =>D5.
 sums,nums,blocks,means,d=aggregate_grid_cells({(5,0):[2.,4.],(6,0):[9.],(5,1):[10.],(5,2):[0.],(5,3):[6.]})
 check('orders_equal_within_grid_grids_equal_not_pooled_rows',means==[6.,10.,0.,6.] and nums==[2,1,1,1])
 check('direction_standardized_D_hand5',d==5.)
 check('block_retains_cell_sums_and_grid_counts',blocks[0][0]==[12.,2] and all(x==[0.,0] for x in blocks[1]))
 days=[{'blocks30min':[[[m,1] for m in vals] for _ in range(48)]} for vals in ([6.,10.,0.,6.],[8.,12.,0.,6.])]
 boot=bootstrap(days,budget)
 check('bootstrap_joint_cells_daystrata_equal_days_hand6',boot['valid_replicates']==1999 and boot['CI_type7_2.5_97.5']==[6.,6.])
 zero={'blocks30min':[[[0.,0] for _ in range(4)] for _ in range(48)]};bootbad=bootstrap([zero,zero],budget)
 check('bootstrap_missing_cells_not_zero_or_resampled_again',bootbad['invalid_replicates']==1999 and not bootbad['minimum1900_pass'])
 flowseq=[tr(base+5*TICK+2000000,src=1,ident=1,typ=0),tr(base+5*TICK+3000000,src=2,ident=2,typ=0),tr(base+5*TICK+4000000,src=3,ident=3,typ=1),tr(base+9*TICK+2000000,src=4,ident=4,typ=0),tr(base+9*TICK+3000000,src=5,ident=5,typ=1)]
 gs,gcounts=grid_states(DATES[0],flowseq,[],budget)
 check('split_trade_counts_not_unique_active_IDs',gs[6][0]=='sell')
 check('zero_score_no_hash_budget',gs[10][0] is None and gs[10][1] is None and gs[10][2]=='zero_score')
 check('no_trades_no_score',gs[7][0] is None and gs[7][2]=='no_trades_no_score')
 check('one_hash_hint_per_same_nonzero_score_grid',gs[6][1] in ('buy','sell'))
 # Stream QC fixtures: identity response, quiet slice, gaps across fixed slices, duplicates/type/CRC failures.
 def native(captext,ident=1,typ=0):return captext+' '+json.dumps({'event':'trade','channel':'live_trades_btcusd','data':{'id':ident,'buy_order_id':100+ident,'sell_order_id':200+ident,'type':typ,'microtimestamp':'100','price_str':'100','amount_str':'1'}})+'\n'
 def piece(text,index=0,encoding='gzip',truncate=False):
  path=fixture/f'{len(list(fixture.iterdir()))}.bin';body=text.encode();body=gzip.compress(body) if encoding=='gzip' else body
  if truncate:body=body[:-4]
  path.write_bytes(body);return {'day':DATES[0],'offset_minutes':index,'path':str(path),'effective_encoding':encoding}
 def state():return {'last':base-1,'pending_gap':False,'gaps':[],'ids':set()}
 original_owner=core_module.OWNER;core_module.OWNER=fixture
 dst=io.StringIO();s=state();q=parse_piece(piece(native('2026-05-01T00:00:00.1000000Z')+'\n'),s,dst,budget)
 parse_piece(piece(native('2026-05-01T00:10:00.1000000Z',2),index=10),s,dst,budget)
 check('disconnect_links_across_slices',s['gaps']==[[base+1000000,base+600*TICK+1000000]])
 check('gzip_identity_same_parser',parse_piece(piece(native('2026-05-01T00:00:00.1000000Z'),encoding='identity'),state(),io.StringIO(),budget)['complete_identity_body'])
 check('empty_valid_gzip_is_quiet_not_gap',parse_piece(piece(''),state(),io.StringIO(),budget)['empty_slice'])
 fails('duplicate_tradeID_rejected',lambda:parse_piece(piece(native('2026-05-01T00:00:00.1000000Z')+native('2026-05-01T00:00:00.2000000Z')),state(),io.StringIO(),budget))
 fails('unknown_type_rejected',lambda:parse_piece(piece(native('2026-05-01T00:00:00.1000000Z',typ=2)),state(),io.StringIO(),budget))
 fails('fixed_slice_boundary_conflict_rejected',lambda:parse_piece(piece(native('2026-05-01T00:10:00.0000000Z')),state(),io.StringIO(),budget))
 fails('truncated_gzip_rejected',lambda:parse_piece(piece(native('2026-05-01T00:00:00.1000000Z'),truncate=True),state(),io.StringIO(),budget))
 core_module.OWNER=original_owner
 fails('nonfinite_price_rejected',lambda:positive_text('NaN'))
 fails('nonpositive_amount_rejected',lambda:positive_text('0'))
 # The test parser appends QC fixtures to an isolated ledger, never actual formal ledger.
 result={'status':'PASS','utc':now(),'checks':passed,'check_count':len(passed),'market_GETs':0,'formal_labels':0,'core_sha256':sha(OWNER/'core.py'),'analysis_sha256':sha(OWNER/'analysis.py'),'tests_sha256':sha(__file__),'synthetic_fixture_directory':str(fixture)}
 write_new(OWNER/f'synthetic-checks-{runid}.json',result);rec=budget.finish('PASS');print(json.dumps({'tests':result,'resource':rec}),flush=True)
except BaseException:
 core_module.OWNER=OWNER
 try:budget.finish('FAIL')
 except BaseException:pass
 raise
