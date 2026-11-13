"""Pure saved-record linkage rules. No Owner imports, no market/label generation."""
import math
from dataclasses import dataclass
from collections import Counter,defaultdict
from decimal import Decimal
T=10_000_000
TOL=1e-12
FIRST=5;LAST=32449
HEADER='t,event,policy,model,delay_ms,order_id,side,limit,quantity,leaves,ahead,order_state,submit,accepted,cancel_sent,cancel_at,cash,BTC,fees,reserved_cash,reserved_BTC,pending_buy_BTC,mid_reference,inventory_price_term,execution_price_term,attribution_fees,detail'.split(',')
def integer(x):
 if isinstance(x,bool):raise ValueError('boolean integer')
 if isinstance(x,int):return x
 if isinstance(x,str) and x.isdigit():return int(x)
 raise ValueError('invalid integer field')
def identity(x):
 n=integer(x)
 if n<=0:raise ValueError('nonpositive ID')
 return n
@dataclass(slots=True)
class Cov:
 ident:int;buy:object;sell:object;side:object;cap:object;src:object;grid:object;status:object;qualified:object;z:object;h:object;label:object
 @classmethod
 def from_row(cls,r):
  return cls(identity(r['tradeID']),r.get('buy_order_id'),r.get('sell_order_id'),r.get('passive_side'),r.get('capture_ticks'),r.get('source_microtimestamp'),r.get('grid_second'),r.get('status'),r.get('reference_qualified'),r.get('z_side'),r.get('hash_side'),r.get('label'))
@dataclass(slots=True)
class Batch:
 row:int;t:int;kind:str;qty:Decimal;price:Decimal;limit:Decimal;accepted:object;cancel:object;ids:tuple;invalid_ids:int;duplicate_ids:bool;order_id:str

def technical(c,b,start):
 if c is None:return 'MISSING_TRADE_ID'
 if c is False:return 'AMBIGUOUS_COVERAGE_KEY'
 try:
  if c.side!='buy':return 'WRONG_PASSIVE_SIDE'
  identity(c.buy);identity(c.sell)
  cap=integer(c.cap);src=integer(c.src);grid=integer(c.grid);accepted=integer(b.accepted)
  if cap!=b.t:return 'CAPTURE_MISMATCH'
  if (cap-start-1)//T!=grid:return 'GRID_CAPTURE_MISMATCH'
  if not b.t>accepted:return 'FILL_NOT_AFTER_ACCEPTED'
  if not src*10>accepted:return 'SOURCE_NOT_AFTER_ACCEPTED'
  if b.cancel not in (None,'',0,'0') and src*10>integer(b.cancel):return 'SOURCE_AFTER_CANCEL_BOUND'
  if b.kind=='equal' and b.price!=b.limit:return 'EQUAL_FILL_LIMIT_MISMATCH'
 except (ValueError,TypeError):return 'MISSING_OR_INVALID_ID_CLOCK'
 return 'MATCHED'

def label_status(c,start):
 try:
  grid=integer(c.grid)
  if not FIRST<=grid<=LAST:return 'OUTSIDE_PRIMARY_GRID'
  if c.status!='selected_first':return 'ORIGINAL_STATUS_'+str(c.status)
  if c.qualified is not True:return 'REFERENCE_UNKNOWN'
  x=c.label
  if not isinstance(x,dict):return 'MISSING_LABEL'
  loss=x.get('loss_bp')
  if isinstance(loss,bool) or not isinstance(loss,(float,int)) or not math.isfinite(loss):return 'INVALID_LABEL_LOSS'
  cap=integer(c.cap);src=integer(c.src);target=integer(x.get('target_ticks'));ref=integer(x.get('capture_ticks'));rsrc=integer(x.get('source_us'))
  if integer(x.get('index'))<0 or integer(x.get('row'))<=0:return 'INVALID_LABEL_REFERENCE_ID'
  if target!=cap+T:return 'LABEL_TARGET_MISMATCH'
  # Only checks of saved internal consistency; no next-BBO/bad/maxsrc reconstruction.
  if ref+10>=target-1:return 'LABEL_CAPTURE_CLOCK_INCONSISTENT'
  if target+1-(ref-10)>T:return 'LABEL_REFERENCE_AGE_INCONSISTENT'
  if rsrc*10-10<=src*10+10:return 'LABEL_SOURCE_CLOCK_INCONSISTENT'
  if c.z not in ('buy','sell',None) or c.h not in ('buy','sell',None):return 'INVALID_ORIGINAL_HINT'
 except (ValueError,TypeError,AttributeError):return 'MISSING_OR_INVALID_LABEL_CLOCK'
 return 'ELIGIBLE'

def evaluate_batch(b,index,start):
 refs=[];eligible={};technical_ids={}
 for ident in b.ids:
  c=index.get(ident);status=technical(c,b,start);reason='NONTRANSFERABLE_CROSS' if b.kind=='cross' else status
  if status=='MATCHED':
   technical_ids[ident]=identity(c.buy)
   reason='NONTRANSFERABLE_CROSS' if b.kind=='cross' else label_status(c,start)
   if reason=='ELIGIBLE':eligible[ident]=c
  refs.append({'tradeID':ident,'technical':status,'transfer':reason,'external_buy_ID':technical_ids.get(ident),'original_status':c.status if isinstance(c,Cov) else None,'original_grid':c.grid if isinstance(c,Cov) else None,'source_us':c.src if isinstance(c,Cov) else None})
 conflict=False
 if b.kind=='equal' and eligible:
  losses=[float(c.label['loss_bp']) for c in eligible.values()]
  conflict=max(losses)-min(losses)>TOL
 if b.duplicate_ids or conflict:
  why='BATCH_DUPLICATE_SOURCE_IDS' if b.duplicate_ids else 'BATCH_LABEL_CONFLICT'
  for r in refs:
   if r['transfer']=='ELIGIBLE':r['transfer']=why
  eligible={}
 # Incomplete/invalid source identities cannot certify any whole batch; known eligible
 # members may remain a support set, never an allocation of the batch fill quantity.
 local_full=bool(b.ids) and not b.invalid_ids and not b.duplicate_ids and not conflict and len(eligible)==len(b.ids)
 return {'refs':refs,'eligible':eligible,'technical_ids':technical_ids,'local_full':local_full,'conflict':conflict}

class Metric:
 def __init__(self):
  self.buy_fills=0;self.buy_qty=Decimal(0);self.fills=Counter();self.qty=defaultdict(Decimal);self.refs=Counter();self.ids={'equal':set(),'cross':set()};self.tech={'equal':{},'cross':{}};self.candidates={};self.batches=[];self.technical_reasons=Counter();self.transfer_reasons=Counter();self.invalid_identity_batches=Counter();self.multi=Counter();self.duplicates=Counter();self.partial=0
 def add(self,b,e):
  self.buy_fills+=1;self.buy_qty+=b.qty;self.fills[b.kind]+=1;self.qty[b.kind]+=b.qty;self.refs[b.kind]+=len(b.ids)+b.invalid_ids;self.ids[b.kind].update(b.ids);self.tech[b.kind].update(e['technical_ids']);self.multi[b.kind]+=len(b.ids)>1;self.duplicates[b.kind]+=b.duplicate_ids;self.invalid_identity_batches[b.kind]+=bool(b.invalid_ids or not b.ids)
  for r in e['refs']:self.technical_reasons[b.kind+'|'+r['technical']]+=1;self.transfer_reasons[b.kind+'|'+r['transfer']]+=1
  if b.kind=='equal':
   self.candidates.update(e['eligible']);self.batches.append((b,e['local_full']))
   if e['eligible'] and not e['local_full']:self.partial+=1
 def finish(self,include_primary=True):
  bybuy=defaultdict(list)
  for ident,c in self.candidates.items():bybuy[identity(c.buy)].append((ident,c))
  ambiguous={buy for buy,v in bybuy.items() if len({i for i,_ in v})>1}
  good={i:c for i,c in self.candidates.items() if identity(c.buy) not in ambiguous}
  goodbuy={identity(c.buy) for c in good.values()};techbuy=set(self.tech['equal'].values())
  denA=len(self.ids['equal']);numA=len(self.tech['equal']);denB=len(techbuy);numB=len(goodbuy)
  A=None if not denA or self.invalid_identity_batches['equal'] else numA/denA;B=None if not denB else numB/denB
  fulln=0;fullq=Decimal(0)
  for b,local in self.batches:
   if local and all(i in good for i in b.ids):fulln+=1;fullq+=b.qty
  cells=[defaultdict(dict),defaultdict(dict)];ids=[set(),set()]
  if include_primary:
   for c in good.values():
    buy=identity(c.buy)
    for j,hint in enumerate((c.z,c.h)):
     if hint=='buy':cells[j][integer(c.grid)][buy]=float(c.label['loss_bp']);ids[j].add(buy)
   means=[];grids=[]
   for v in cells:
    gm=[math.fsum(m.values())/len(m) for _,m in sorted(v.items())];grids.append(len(gm));means.append(math.fsum(gm)/len(gm) if gm else None)
   D=None if any(x is None for x in means) else means[0]-means[1]
  else:ids=[set(),set()];grids=[];means=[None,None];D=None
  apass=A is not None and numA*5>=denA*4;bpass=B is not None and numB*5>=denB*4;npass=all(len(s)>=100 for s in ids)
  def ratio(n,d):return None if not d else n/d
  out={'all_maker_buy_fill_records':self.buy_fills,'all_maker_buy_BTC_qty':str(self.buy_qty),'equal_cross_fill_records':dict(self.fills),'equal_cross_BTC_qty':{k:str(v) for k,v in self.qty.items()},'all_source_references_including_invalid':dict(self.refs),'unique_tradeIDs':{k:len(v) for k,v in self.ids.items()},'technical_unique_tradeIDs':{k:len(v) for k,v in self.tech.items()},'multiID_batches':dict(self.multi),'internal_duplicate_batches':dict(self.duplicates),'unidentifiable_ID_batches':dict(self.invalid_identity_batches),'technical_reason_reference_counts':dict(self.technical_reasons),'transfer_reason_reference_counts':dict(self.transfer_reasons),'A_technical_coverage':{'numerator':numA,'denominator_known_equal_unique_tradeIDs':denA,'ratio':A,'unknown_ID_denominator':bool(self.invalid_identity_batches['equal']),'pass80':apass},'B_first_ID_coverage':{'numerator':numB,'denominator_technical_unique_external_buyIDs':denB,'ratio':B,'pass80':bpass},'raw_label_candidate_tradeIDs_before_external_ID_conflict':len(self.candidates),'external_first_ID_ambiguities':len(ambiguous),'qualified_supported_tradeIDs':len(good),'qualified_tradeID_over_all_equal_unique_tradeID':ratio(len(good),denA),'partial_label_batches':self.partial,'whole_batch':{'equal_fill_records':fulln,'BTC_qty':str(fullq),'over_equal_fill_ratio':ratio(fulln,self.fills['equal']),'over_all_buy_fill_ratio':ratio(fulln,self.buy_fills),'qty_over_equal_buy_qty':None if not self.qty['equal'] else str(fullq/self.qty['equal']),'qty_over_all_buy_qty':None if not self.buy_qty else str(fullq/self.buy_qty)},'primary':{'group_order':['z_buy','hash_buy'],'distinct_external_buyIDs':[len(x) for x in ids],'valid_grid_counts':grids,'overlap_external_buyIDs':len(ids[0]&ids[1]),'L_z_buy':means[0],'L_hash_buy':means[1],'D_buy':D,'A_pass80':apass,'B_pass80':bpass,'both_groups_min100_pass':npass,'descriptive_eligibility':'ELIGIBLE' if apass and bpass and npass else 'INSUFFICIENT_COVERAGE_OR_SAMPLE','interpretation':None if not(apass and bpass and npass) or D is None else 'DIRECTION_RETAINED' if D>0 else 'POSITIVE_DIFFERENCE_NOT_RETAINED'},'cross_transferred_label_count':0}
  if not include_primary:out.pop('primary')
  return out
