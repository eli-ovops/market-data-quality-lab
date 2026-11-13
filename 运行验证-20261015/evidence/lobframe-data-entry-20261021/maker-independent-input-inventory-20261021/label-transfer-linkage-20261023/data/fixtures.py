"""Artificial IDs/clocks/labels only; never opens any real input body."""
from decimal import Decimal
from dataclasses import replace
from linkage_core import Cov,Batch,Metric,evaluate_batch,technical,label_status,T

def cov(ident=1,buy=101,cap=6*T+1000,loss=2.,z='buy',h='sell',status='selected_first',qualified=True):
 src=cap//10-100
 return Cov(ident,str(buy),'901','buy',cap,src,(cap-1)//T,status,qualified,z,h,{'index':0,'row':1,'capture_ticks':cap+T-1000,'source_us':src+900000,'target_ticks':cap+T,'loss_bp':loss} if qualified else None)
def batch(ids=(1,),kind='equal',cap=6*T+1000,invalid=0,duplicate=False):
 return Batch(1,cap,kind,Decimal('1'),Decimal('100'),Decimal('100'),cap-T,'',tuple(ids),invalid,duplicate,'synthetic-order-1')
def metric(b,index):
 m=Metric();m.add(b,evaluate_batch(b,index,0));return m.finish()
def run():
 tests=[]
 def check(name,ok):
  tests.append({'name':name,'pass':bool(ok)})
  if not ok:raise AssertionError(name)
 c=cov();b=batch();e=evaluate_batch(b,{1:c},0);m=metric(b,{1:c})
 check('single_equal_exact_identity_label',len(e['eligible'])==1 and e['local_full'] and m['A_technical_coverage']['ratio']==1 and m['B_first_ID_coverage']['ratio']==1)
 check('missing_source_ID_preserves_denominator',metric(b,{})['A_technical_coverage']['denominator_known_equal_unique_tradeIDs']==1 and metric(b,{})['A_technical_coverage']['numerator']==0)
 check('duplicate_coverage_key_ambiguous',technical(False,b,0)=='AMBIGUOUS_COVERAGE_KEY')
 check('wrong_side_rejected',technical(replace(c,side='sell'),b,0)=='WRONG_PASSIVE_SIDE')
 check('capture_mismatch_rejected',technical(replace(c,cap=c.cap+1),b,0)=='CAPTURE_MISMATCH')
 check('grid_formula_mismatch_rejected',technical(replace(c,grid=7),b,0)=='GRID_CAPTURE_MISMATCH')
 check('fill_equal_accepted_not_strict',technical(c,replace(b,accepted=b.t),0)=='FILL_NOT_AFTER_ACCEPTED')
 check('source_equal_accepted_not_strict',technical(c,replace(b,accepted=c.src*10),0)=='SOURCE_NOT_AFTER_ACCEPTED')
 check('saved_cancel_source_bound_rejected',technical(c,replace(b,cancel=c.src*10-1),0)=='SOURCE_AFTER_CANCEL_BOUND')
 check('equal_saved_limit_mismatch',technical(c,replace(b,limit=Decimal('99')),0)=='EQUAL_FILL_LIMIT_MISMATCH')
 check('no_extra_source_before_capture_rule',technical(replace(c,src=c.cap//10+100),b,0)=='MATCHED')
 r=replace(c,status='reference_UNKNOWN',qualified=False,label=None)
 check('reference_unknown_not_zero',not evaluate_batch(b,{1:r},0)['eligible'])
 r=replace(c,status='later_passive_ID_not_weighted')
 check('later_ID_not_reselected',not evaluate_batch(b,{1:r},0)['eligible'] and metric(b,{1:r})['B_first_ID_coverage']['denominator_technical_unique_external_buyIDs']==1)
 x=cov(ident=2,buy=102,loss=2.+2e-12)
 e=evaluate_batch(batch((1,2)),{1:c,2:x},0)
 check('multiID_label_conflict_rejects_all_candidates',e['conflict'] and not e['eligible'])
 x=cov(ident=2,buy=102,loss=2.+5e-13)
 check('absolute_tolerance_same_batch',len(evaluate_batch(batch((1,2)),{1:c,2:x},0)['eligible'])==2)
 x=cov(ident=2,buy=102,status='later_passive_ID_not_weighted')
 m=metric(batch((1,2)),{1:c,2:x})
 check('partial_batch_support_no_qty_expansion',m['qualified_supported_tradeIDs']==1 and m['whole_batch']['equal_fill_records']==0 and m['whole_batch']['BTC_qty']=='0')
 e=evaluate_batch(batch(duplicate=True),{1:c},0)
 check('internal_duplicate_batch_multivalued_no_transfer',not e['eligible'] and e['refs'][0]['transfer']=='BATCH_DUPLICATE_SOURCE_IDS')
 m=metric(batch(invalid=1),{1:c})
 check('unknown_identity_A_not_false_full_coverage',m['A_technical_coverage']['ratio'] is None and m['A_technical_coverage']['unknown_ID_denominator'])
 e=evaluate_batch(batch(kind='cross'),{1:c},0);m=metric(batch(kind='cross'),{1:c})
 check('cross_always_nontransferable_even_technical_hit',e['refs'][0]['technical']=='MATCHED' and e['refs'][0]['transfer']=='NONTRANSFERABLE_CROSS' and not e['eligible'] and m['cross_transferred_label_count']==0)
 check('cross_missing_still_nontransferable',evaluate_batch(batch(kind='cross'),{},0)['refs'][0]['transfer']=='NONTRANSFERABLE_CROSS')
 x=replace(c,label={**c.label,'target_ticks':c.cap+T+1})
 check('target_not_recomputed',label_status(x,0)=='LABEL_TARGET_MISMATCH')
 x=replace(c,label={**c.label,'source_us':c.src+1})
 check('saved_label_source_clock_consistency',label_status(x,0)=='LABEL_SOURCE_CLOCK_INCONSISTENT')
 x=replace(c,label={**c.label,'loss_bp':float('nan')})
 check('nonfinite_old_label_rejected',label_status(x,0)=='INVALID_LABEL_LOSS')
 x=replace(c,grid=32450,cap=32450*T+1000,src=3245000000)
 check('out_of_primary_window_kept_as_reason',label_status(x,0)=='OUTSIDE_PRIMARY_GRID')
 m=Metric();m.add(b,evaluate_batch(b,{1:c},0));m.add(b,evaluate_batch(b,{1:c},0));r=m.finish()
 check('cross_arm_same_trade_dedup_no_independent_inflation',r['all_maker_buy_fill_records']==2 and r['unique_tradeIDs']['equal']==1 and r['primary']['distinct_external_buyIDs']==[1,0])
 x=cov(ident=2,buy=101)
 m=Metric();m.add(b,evaluate_batch(b,{1:c},0));b2=batch((2,));m.add(b2,evaluate_batch(b2,{2:x},0));r=m.finish()
 check('different_selected_first_same_external_ID_ambiguous',r['external_first_ID_ambiguities']==1 and r['qualified_supported_tradeIDs']==0)
 r=Metric().finish()
 check('empty_denominator_unknown_not_zero',r['A_technical_coverage']['ratio'] is None and r['primary']['D_buy'] is None and r['primary']['descriptive_eligibility']=='INSUFFICIENT_COVERAGE_OR_SAMPLE')
 # 3 distinct external IDs: grid6 average(1,3)=2; grid7 average5 => z mean3.5.
 # hash selects only loss1 and5 => hash mean3; overlap2. No half or sell contribution.
 m=Metric()
 for i,loss,cap,z,h in [(1,1.,6*T+1000,'buy','buy'),(2,3.,6*T+1000,'buy','sell'),(3,5.,7*T+1000,'buy','buy')]:
  cc=cov(i,100+i,cap,loss,z,h);bb=batch((i,),cap=cap);m.add(bb,evaluate_batch(bb,{i:cc},0))
 r=m.finish();pp=r['primary']
 check('external_ID_within_grid_then_grid_equal_primary',pp['L_z_buy']==3.5 and pp['L_hash_buy']==3 and pp['D_buy']==.5 and pp['overlap_external_buyIDs']==2)
 check('minimum100_not_relaxed',not pp['both_groups_min100_pass'] and pp['descriptive_eligibility']=='INSUFFICIENT_COVERAGE_OR_SAMPLE')
 check('path_primary_means_not_computed_or_published','primary' not in m.finish(False))
 # Membership boundary is strict t<freeze; no completion from freeze onward.
 cutoff=b.t
 check('frozen_common_prefix_strict_boundary',not(b.t<cutoff) and b.t-1<cutoff)
 # Tiny ARTIFICIAL files exercise the actual stream/schema/hash/CRC and frozen join.
 import json,gzip,csv,io,hashlib
 from pathlib import Path
 import linkage as stream
 from linkage_core import HEADER
 class NoopGuard:
  def check(self,*a):pass
 stream.guard=NoopGuard()
 out=Path(__file__).resolve().parent/'synthetic-fixtures';out.mkdir(exist_ok=False)
 cp=out/'coverage.jsonl.gz'
 cc=cov();row={'tradeID':str(cc.ident),'buy_order_id':cc.buy,'sell_order_id':cc.sell,'passive_side':cc.side,'capture_ticks':cc.cap,'source_microtimestamp':cc.src,'grid_second':cc.grid,'status':cc.status,'reference_qualified':cc.qualified,'z_side':cc.z,'hash_side':cc.h,'label':cc.label}
 with gzip.open(cp,'wt') as f:f.write(json.dumps(row)+'\n')
 def src(path,kind,n):return {'path':str(path),'kind':kind,'day':'1970-01-01','sealed_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sealed_compressed_bytes':path.stat().st_size,'sealed_data_rows_excluding_CSV_header_if_any':n}
 cs=src(cp,'coverage',1);ci,cr=stream.read_coverage(cs)
 check('actual_artificial_coverage_stream_SHA_CRC',ci[1].ident==1 and cr['gzip_EOF_CRC'] and cr['data_rows']==1)
 lp=out/'ledger.csv.gz';rr=['']*len(HEADER);pos={v:i for i,v in enumerate(HEADER)}
 for k,v in {'t':str(b.t),'event':'fill','model':'E','delay_ms':'100','policy':'F1','order_id':'synthetic-1','side':'buy','limit':'100','accepted':str(b.t-T),'detail':json.dumps({'fill_kind':'equal','qty':'1','fill_price':'100','trade_ids':[1]})}.items():rr[pos[k]]=v
 with gzip.open(lp,'wt',newline='') as f:w=csv.writer(f);w.writerow(HEADER);w.writerow(rr)
 ls=src(lp,'inventory_exit_ledger',1);inv={'path_universe':[{'day':'1970-01-01','model':m,'delay_ms':delay,'policy':policy,'frozen':False,'execution_cash_status':'ARTIFICIAL'} for m in ('E','X') for delay in (100,500) for policy in ('F1','H1')]};cuts={('1970-01-01',m,delay):None for m in ('E','X') for delay in (100,500)}
 pp,ce,wi,lr=stream.read_day_ledger(ls,ci,inv,cuts,io.StringIO())
 actual=next(x for x in ce if x['model']=='E' and x['delay_ms']==100)
 check('actual_artificial_ledger_stream_same_id_join',len(pp)==8 and actual['metrics']['A_technical_coverage']['numerator']==1 and lr['gzip_EOF_CRC'])
 cuts[('1970-01-01','E',100)]=b.t
 pp,ce,wi,lr=stream.read_day_ledger(ls,ci,inv,cuts,io.StringIO());actual=next(x for x in ce if x['model']=='E' and x['delay_ms']==100);path=next(x for x in pp if x['model']=='E' and x['delay_ms']==100 and x['policy']=='F1')
 check('actual_frozen_boundary_excludes_cell_preserves_saved_path',actual['metrics']['all_maker_buy_fill_records']==0 and path['all_saved_maker_buy_coverage']['all_maker_buy_fill_records']==1 and actual['metrics']['primary']['full_window_eligibility']=='UNKNOWN_FROZEN')
 bad={**cs,'sealed_sha256':'0'*64};rejected=False
 try:stream.read_coverage(bad)
 except ValueError:rejected=True
 check('actual_stream_SHA_mismatch_stops',rejected)
 bp=out/'bad-CRC.jsonl.gz';raw=bytearray(cp.read_bytes());raw[-8]^=1;bp.write_bytes(raw);rejected=False
 try:stream.read_coverage(src(bp,'coverage',1))
 except (gzip.BadGzipFile,EOFError):rejected=True
 check('actual_stream_bad_CRC_stops',rejected)
 stream.save('synthetic-fixtures/exclusive-marker.json',{'artificial':True});rejected=False
 try:stream.save('synthetic-fixtures/exclusive-marker.json',{'artificial':True})
 except FileExistsError:rejected=True
 check('same_exclusive_save_blocks_second_marker',rejected)
 return tests
