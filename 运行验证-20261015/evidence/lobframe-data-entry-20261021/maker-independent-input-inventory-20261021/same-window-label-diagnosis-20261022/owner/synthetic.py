"""Only invented stored-row fixtures; no real coverage, sources, labels or prices opened."""
from aggregate import Aggregate,validate_row,bootstrap,type7,T
import math

def row(g=5,side='buy',loss=1.,z=None,h=None,status='selected_first',ident='X',qualified=True,capture=None):
 return {'grid_second':g,'capture_ticks':g*T+1 if capture is None else capture,'passive_side':side,'buy_order_id':ident,'sell_order_id':ident,'z_side':z,'hash_side':h,'status':status,'reference_qualified':qualified,'label':{'loss_bp':loss} if qualified else None,'grid_reason':None if z else 'zero_score'}
def run():
 out=[]
 def check(n,f):f();out.append({'name':n,'pass':True})
 def eq(a,b):assert a==b,(a,b)
 def raises(f):
  try:f()
  except ValueError:return
  raise AssertionError('Expected invalid stored mapping')
 def endpoints():
  a=Aggregate(5,32449,19)
  for g in (4,5,32449,32450):a.add(row(g,z='buy',ident=str(g)))
  r=a.result();eq(r['fixed_label_denominator'],2);eq(r['cell_selected_order_counts'][0],2);eq(r['blocks30min'][0][0][1],1);eq(r['blocks30min'][18][0][1],1)
 check('both end grids included full lastsecond edges retained no extension',endpoints)
 check('capture lowerplus1 maps originalgrid',lambda:validate_row(row(capture=5*T+1),0))
 check('capture exactupper maps originalgrid',lambda:validate_row(row(capture=6*T),0))
 check('capture at lower belongs priorgrid rejected mismatch',lambda:raises(lambda:validate_row(row(capture=5*T),0)))
 def no_replace():
  a=Aggregate(5,32449,19);a.add(row(4,z='buy',ident='same'));a.add(row(5,z='buy',status='later_passive_ID_not_weighted',loss=999.,ident='same'));r=a.result();eq(r['fixed_label_denominator'],1);eq(r['cell_selected_order_counts'],[0,0,0,0])
 check('original firstoutside window laterID never substitute',no_replace)
 def statuses():
  a=Aggregate(5,32449,19)
  a.add(row(z='buy',status='reference_UNKNOWN',qualified=False));a.add(row(z='buy',status='first_capture_tie_UNKNOWN'));a.add(row(6,status='selected_first',ident='nohint'))
  r=a.result();eq(r['fixed_label_denominator'],3);eq(r['reference_qualified_numerator'],2);eq(r['reference_UNKNOWN_count'],1);eq(r['cell_selected_order_counts'],[0,0,0,0])
 check('UNKNOWN tie and zero nohint retained denominator never0loss',statuses)
 def weighted():
  a=Aggregate(5,32449,19)
  examples=[row(5,loss=1,z='buy',h='sell',ident='a'),row(5,loss=3,z='buy',h='sell',ident='b'),row(6,loss=10,z='buy',h='sell',ident='c'),row(5,side='sell',loss=4,z='sell',h='buy',ident='d'),row(5,loss=2,z='sell',h='buy',ident='e'),row(6,loss=2,z='sell',h='buy',ident='f'),row(5,side='sell',loss=2,z='buy',h='sell',ident='g')]
  for r in examples:a.add(r)
  r=a.result();eq(r['L_policy_direction'],[6.,4.,2.,2.]);eq(r['D_day_bp'],3.);eq(r['cell_selected_order_counts'],[3,1,2,1]);eq(r['cell_valid_grid_counts'],[2,1,2,1])
 check('orders within grid then equalgrids then equaldirections handD3',weighted)
 def empty():
  a=Aggregate(5,32449,19);a.add(row(z='buy'));r=a.result();eq(r['D_day_bp'],None);eq(r['L_policy_direction'][1],None);eq(r['minimum100_IDs_eachcell_pass'],False)
 check('missing cell DUNKNOWN not zero direction',empty)
 check('type7 handquantile',lambda:eq(type7(list(range(10)),.5),4.5))
 def blocks():
  b=[[[3.,1],[3.,1],[1.,1],[1.,1]] for _ in range(19)]
  r=bootstrap([{'blocks30min':b},{'blocks30min':b}]);eq(r['daily'][0]['valid_replicates'],1999);eq(r['daily'][1]['CI_type7_2_5_97_5'],[2.,2.]);eq(r['equal_two_day_auxiliary']['CI_type7_2_5_97_5'],[2.,2.])
 check('19jointcell blocks constantD2 pairedbootstrap preserved',blocks)
 def nozero():
  b=[[[0.,0] for _ in range(4)] for _ in range(19)];r=bootstrap([{'blocks30min':b},{'blocks30min':b}],R=3)
  eq(r['daily'][0]['valid_replicates'],0);eq(r['daily'][0]['CI_type7_2_5_97_5'],None);eq(r['equal_two_day_auxiliary']['valid_replicates'],0)
 check('invalid resample no0 substitution ownpaired validity',nozero)
 def invalid_selected():
  a=Aggregate(5,32449,19);raises(lambda:a.add(row(z='buy',qualified=False)))
 check('cannot invent label for invalidselected row',invalid_selected)
 return out
