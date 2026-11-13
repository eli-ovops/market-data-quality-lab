"""Fixed flow rule, uncertain-clock labels, per-order weighting, stratified D."""
from core import *

@dataclass(slots=True)
class BBO:
 cap:object;src:object;row:object;bad:object;bid:list;ask:list;meta:dict

def load_bbo(item,budget):
 caps=array.array('q');sources=array.array('q');rows=array.array('I');bad=array.array('B');bids=[];asks=[]
 prior=None;prior_source=None;max_source=-1;group=None;total=0;source_regressions=0;conflicts=0
 def put(g):
  nonlocal conflicts
  t,src,rowno,vals,valid,conflict,regressed=g
  caps.append(t);sources.append(src);rows.append(rowno);bad.append(int(not valid or conflict or regressed));bids.append(vals[0]);asks.append(vals[1]);conflicts+=int(conflict)
 with gzip.open(item['path'],'rt',newline='') as f:
  for i,r in enumerate(csv.DictReader(f),1):
   total=i;t=int(r['local_timestamp'])*10;src=int(r['timestamp']);valid=True
   try:
    vals=tuple(positive_text(r[k]) for k in ('bids[0].price','asks[0].price','bids[0].amount','asks[0].amount'))
    if Decimal(vals[1])<Decimal(vals[0]):valid=False
   except Exception:vals=('0','0','0','0');valid=False
   if prior is not None and t<prior:raise RuntimeError('BBO capture regression')
   regressed=src<max_source;source_regressions+=int(regressed);max_source=max(max_source,src)
   conflict=False
   if group is not None:
    if t==group[0]:
     conflict=group[5] or tuple(Decimal(v) for v in vals)!=tuple(Decimal(v) for v in group[3]);regressed=regressed or group[6];valid=valid and group[4]
    else:put(group)
   group=(t,src,i,vals,valid,conflict,regressed);prior=t;prior_source=src
   if i%10000==0:budget.guard()
 if group is not None:put(group)
 if total!=item['rows']:raise RuntimeError('BBO row count drift')
 return BBO(caps,sources,rows,bad,bids,asks,{'rows':total,'groups':len(caps),'conflicting_capture_groups':conflicts,'source_regression_rows':source_regressions,'gzip_EOF_CRC':True})


def label_reference(trade,bbo):
 target=trade.cap+TICK;j=bisect.bisect_right(bbo.cap,target)-1
 if j<0:return None,'no_asof_BBO'
 ref=bbo.cap[j]
 # Never fall back to an older favorable row when the latest nominal row is uncertain.
 if ref+10>=target-1:return None,'asof_capture_intervals_overlap'
 if j+1<len(bbo.cap) and bbo.cap[j+1]-10<=target+1:return None,'next_BBO_capture_uncertain_at_target'
 if target+1-(ref-10)>TICK:return None,'BBO_worst_age_over_1s'
 if bbo.bad[j]:return None,'BBO_invalid_conflict_or_source_regression'
 if bbo.src[j]*10-10<=trade.src*10+10:return None,'BBO_source_not_strictly_later'
 bid=float(bbo.bid[j]);ask=float(bbo.ask[j]);p=float(trade.price);mid=(bid+ask)/2
 loss=(mid-p)/p*10000 if trade.typ==0 else (p-mid)/p*10000
 if not math.isfinite(loss):raise RuntimeError('Nonfinite adverse label')
 return {'index':j,'row':bbo.row[j],'capture_ticks':ref,'source_us':bbo.src[j],'target_ticks':target,'loss_bp':loss},None


def auxiliary(trade,bbo,label):
 p=Fraction(trade.price);j=label['index'];buy_passive=trade.typ==1
 if buy_passive:
  ratio=Fraction(bbo.bid[j])*Fraction(9999,10000)/p
  main=10000*(ratio*Fraction(996,1000)-Fraction(1003,1000));zero=10000*(ratio-1)
 else:
  ratio=Fraction(bbo.ask[j])*Fraction(10001,10000)/p
  main=10000*(Fraction(997,1000)-ratio*Fraction(1004,1000));zero=10000*(1-ratio)
 return main,zero

def fraction_text(x):
 from decimal import localcontext
 with localcontext() as c:c.prec=48;return str(Decimal(x.numerator)/Decimal(x.denominator))


def gap_intersects(t,gaps):return any(a<t and b>=t-TICK for a,b in gaps)

def ambiguous_boundary(caps,boundary):
 # Native intervals +/-1 tick; lower window endpoint included, upper excluded.
 j=bisect.bisect_left(caps,boundary-1)
 return j<len(caps) and caps[j]-1<boundary<=caps[j]+1

def grid_states(day,trades,gaps,budget):
 caps=[x.cap for x in trades];prefix=[];maximum=-1
 for x in trades:maximum=max(maximum,x.src);prefix.append(maximum)
 states={};counts=Counter();start=day0(day)
 for second in range(5,86395):
  t=start+second*TICK;a=bisect.bisect_left(caps,t-TICK);b=bisect.bisect_left(caps,t)
  maxsrc=prefix[b-1] if b else None
  reason=None;side=None
  if gap_intersects(t,gaps):reason='explicit_disconnect_input_window'
  elif ambiguous_boundary(caps,t-TICK) or ambiguous_boundary(caps,t):reason='input_capture_boundary_uncertain'
  elif a==b:reason='no_trades_no_score'
  else:
   buy=sum(x.typ==0 for x in trades[a:b]);sell=b-a-buy
   side='sell' if buy>sell else 'buy' if sell>buy else None
   if side is None:reason='zero_score'
  text='XTX-adverse-proxy-v1|'+datetime.fromtimestamp(t//TICK,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
  hashside=('buy' if hashlib.sha256(text.encode('utf-8')).digest()[0]<128 else 'sell') if side else None
  states[second]=(side,hashside,reason,maxsrc)
  counts[reason or 'nonzero_score']+=1
  if second%5000==0:budget.guard()
 return states,dict(counts)


def source_anchors(day,trades):
 caps=[x.cap for x in trades];prefix=[];maximum=-1
 for tr in trades:maximum=max(maximum,tr.src);prefix.append(maximum)
 result={};start=day0(day)
 for second in range(5,86395):
  n=bisect.bisect_left(caps,start+second*TICK)
  result[second]=(None,None,None,prefix[n-1] if n else None)
 return result


def future_time_guard(day,trade,state):
 rel=trade.cap-day0(day);second=(rel-1)//TICK;t=day0(day)+second*TICK
 if not 5<=second<=86394:return int(second),'outside_fixed_observation_domain'
 if trade.cap-1<=t or trade.cap+1>t+TICK:return int(second),'future_capture_boundary_uncertain'
 maxsrc=state[second][3]
 if maxsrc is None:return int(second),'no_known_source_anchor'
 if trade.src<=maxsrc:return int(second),'future_source_not_after_all_known_max'
 return int(second),None


def choose_first(candidates,trades):
 # Candidate eligibility independent of z/hash: no-score/zero-score cannot select a later fill.
 first={};ties=set()
 for i in candidates:
  tr=trades[i];ident=tr.sell if tr.typ==0 else tr.buy
  if ident not in first:first[ident]=i
  elif trades[first[ident]].cap==tr.cap:ties.add(ident)
 return {i for ident,i in first.items() if ident not in ties},ties


def cell_index(policy,side):return (0 if policy=='z' else 2)+(0 if side=='buy' else 1)

def type7(values,q):
 vals=sorted(values);pos=(len(vals)-1)*q;i=int(pos);f=pos-i
 return vals[i]+(vals[min(i+1,len(vals)-1)]-vals[i])*f


def analyze_day(item,seal,budget):
 day=item['date'];trades=[]
 with gzip.open(seal['normalized_path'],'rt') as f:
  for line in f:trades.append(Trade(*json.loads(line)))
 if len(trades)!=seal['trade_count']:raise RuntimeError('Sealed raw trade count mismatch')
 bbo=load_bbo(item,budget);states=source_anchors(day,trades)
 counts=Counter();reasons=Counter();labels={};time_ok=[];time_reason={};cost=Counter();cost_min={};cost_max={};start=day0(day)
 for i,tr in enumerate(trades):
  if not start+5*TICK<tr.cap<=start+86395*TICK:counts['outside_denominator_boundary']+=1;continue
  counts['fixed_trade_denominator']+=1
  label,reason=label_reference(tr,bbo)
  if label is None:reasons[reason]+=1;continue
  labels[i]=label;counts['qualified_future_reference_labels']+=1
  main,zero=auxiliary(tr,bbo,label)
  for name,value in (('main',main),('zero_fee_exit_slip_retained',zero)):
   cost[name+'_positive' if value>0 else name+'_negative' if value<0 else name+'_zero']+=1
   if name not in cost_min or value<cost_min[name][0]:cost_min[name]=(value,i)
   if name not in cost_max or value>cost_max[name][0]:cost_max[name]=(value,i)
  sec,why=future_time_guard(day,tr,states)
  if why:time_reason[i]=why;counts[why]+=1
  else:time_ok.append(i)
  if i%2000==0:budget.guard()
 denom=counts['fixed_trade_denominator'];qualified=counts['qualified_future_reference_labels']
 if denom==0 or qualified*5<denom*4:
  summary={'date':day,'input_status':'INDETERMINATE_LABEL_COVERAGE','fixed_denominator':denom,'label_coverage_numerator':qualified,'label_coverage_pass_80pct':False,'counts':dict(counts),'reference_unknown_reasons':dict(reasons),'flow_hints_not_run':True,'BBO_metadata':bbo.meta}
  with gzip.open(OWNER/f'{day}-reference-only-coverage.jsonl.gz','xt') as out:
   for i,tr in enumerate(trades):
    if start+5*TICK<tr.cap<=start+86395*TICK:out.write(json.dumps({'tradeID':str(tr.id),'capture_ticks':tr.cap,'source_microtimestamp':tr.src,'reference_qualified':i in labels,'reference':labels.get(i)},separators=(',',':'))+'\n')
  write_new(OWNER/f'{day}-summary.json',summary);return summary
 states,gridcounts=grid_states(day,trades,seal['disconnect_intervals_closed'],budget)
 selected,tied=choose_first(time_ok,trades);counts['first_time_reference_qualified_unique_passive_IDs']=len(selected);counts['first_capture_tied_passive_IDs_UNKNOWN']=len(tied)
 cells=defaultdict(list);observation_counts=Counter();id_sets=[set() for _ in range(4)];background=[]
 coverage_path=OWNER/f'{day}-coverage.jsonl.gz'
 with gzip.open(coverage_path,'xt') as f:
  for i,tr in enumerate(trades):
   if not start+5*TICK<tr.cap<=start+86395*TICK:continue
   ident=tr.sell if tr.typ==0 else tr.buy;side='sell' if tr.typ==0 else 'buy';sec=(tr.cap-start-1)//TICK
   state=states[int(sec)];label=labels.get(i);status='reference_UNKNOWN' if label is None else time_reason.get(i)
   if label is not None and status is None:
    status='first_capture_tie_UNKNOWN' if ident in tied else 'selected_first' if i in selected else 'later_passive_ID_not_weighted'
   row={'tradeID':str(tr.id),'buy_order_id':str(tr.buy),'sell_order_id':str(tr.sell),'passive_side':side,'capture_ticks':tr.cap,'source_microtimestamp':tr.src,
        'raw_offset_minutes':tr.slice,'raw_line':tr.line,'grid_second':int(sec),'reference_qualified':label is not None,'status':status,
        'z_side':state[0],'hash_side':state[1],'grid_reason':state[2],'label':label}
   if label is not None:
    main,zero=auxiliary(tr,bbo,label);row['aux_main_bp']=fraction_text(main);row['aux_zero_fee_bp']=fraction_text(zero)
   f.write(json.dumps(row,separators=(',',':'))+'\n')
   if i in selected:
    background.append(label['loss_bp'])
    for policy,hint in (('z',state[0]),('hash',state[1])):
     if hint==side:
      cell=cell_index(policy,side);cells[(int(sec),cell)].append(label['loss_bp']);id_sets[cell].add(ident);observation_counts[policy+'_'+side]+=1
 # Every eligible grid first averages orders equally, then grids equally for each direction/policy.
 sums=[0.]*4;nums=[0]*4;blocks=[[[0.,0] for _ in range(4)] for _ in range(48)]
 for (second,cell),losses in cells.items():
  mean=math.fsum(losses)/len(losses);sums[cell]+=mean;nums[cell]+=1;blocks[second//1800][cell][0]+=mean;blocks[second//1800][cell][1]+=1
 means=[sums[k]/nums[k] if nums[k] else None for k in range(4)]
 d=None if any(x is None for x in means) else .5*((means[0]-means[2])+(means[1]-means[3]))
 denom=counts['fixed_trade_denominator'];qualified=counts['qualified_future_reference_labels'];coverage_pass=denom>0 and qualified*5>=denom*4
 minimum_ids=all(len(ids)>=100 for ids in id_sets)
 def cost_witness(v):
  value,i=v;tr=trades[i];return {'bp':fraction_text(value),'tradeID':str(tr.id),'capture_ticks':tr.cap,'source_microtimestamp':tr.src,'reference':labels[i],'raw_offset_minutes':tr.slice,'raw_line':tr.line}
 summary={'date':day,'counts':dict(counts),'reference_unknown_reasons':dict(reasons),'grid_counts':gridcounts,'fixed_denominator':denom,'label_coverage_numerator':qualified,
  'label_coverage_pass_80pct':coverage_pass,'minimum100_independent_passive_IDs_each_policy_direction':minimum_ids,
  'cell_order':['z_buy','z_sell','hash_buy','hash_sell'],'independent_ID_counts':[len(x) for x in id_sets],'selected_observation_counts':dict(observation_counts),
  'valid_grid_counts':nums,'sum_of_grid_order_means':sums,'L_policy_direction':means,'D_day':d,'blocks30min':blocks,
  'background_selected_first_order_count':len(background),'background_mean_loss_bp':math.fsum(background)/len(background) if background else None,
  'auxiliary_all_reference_qualified_trade_counts':dict(cost),'auxiliary_min_witness':{k:cost_witness(v) for k,v in cost_min.items()},'auxiliary_max_witness':{k:cost_witness(v) for k,v in cost_max.items()},
  'auxiliary_does_not_gate_flow_statistics':True,'BBO_metadata':bbo.meta,'coverage_path':str(coverage_path),'coverage_sha256':sha(coverage_path)}
 write_new(OWNER/f'{day}-summary.json',summary);return summary


def bootstrap(days,budget):
 rng=random.Random(20261021);values=[];invalid=0;draws_hash=hashlib.sha256()
 for rep in range(1999):
  ds=[]
  for day in days:
   sums=[0.]*4;counts=[0]*4;indices=[rng.randrange(48) for _ in range(48)];draws_hash.update(bytes(indices))
   for i in indices:
    for cell in range(4):sums[cell]+=day['blocks30min'][i][cell][0];counts[cell]+=day['blocks30min'][i][cell][1]
   if any(n==0 for n in counts):ds.append(None)
   else:
    means=[sums[k]/counts[k] for k in range(4)];ds.append(.5*((means[0]-means[2])+(means[1]-means[3])))
  if any(d is None for d in ds):invalid+=1
  else:values.append(.5*(ds[0]+ds[1]))
  if rep%200==0:budget.guard()
 return {'method':'within each day sample48 nonoverlapping30minute blocks with replacement, joint four-cell sums/counts, equal two-day D',
  'RNG':'stdlib random.Random(20261021), randrange(48), dayMay thenJun per replicate','replicates':1999,'valid_replicates':len(values),'invalid_replicates':invalid,
  'minimum1900_pass':len(values)>=1900,'CI_type7_2.5_97.5':[type7(values,.025),type7(values,.975)] if len(values)>=1900 else None,'draws_sha256':draws_hash.hexdigest()}
