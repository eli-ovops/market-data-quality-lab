"""Only amendment boundary tests: artificial identities and isolated fake Budget failure."""
import importlib.util,sys,copy
from pathlib import Path
p=Path(__file__).with_name('stage0.py')
spec=importlib.util.spec_from_file_location('stage0',p);s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s)
budget=s.Budget('protection-fix-tests');checks=[]
def check(name,value):
    if not value:raise AssertionError(name)
    checks.append(name)
try:
    sealed=[{'date':day,'path':f'/artificial-only/{day}.csv.gz','expected_rows':123,'expected_sha256':'a'*64,'actual_sha256':'a'*64} for day in s.DATES]
    current=[{k:v for k,v in x.items() if k!='actual_sha256'} for x in sealed]
    check('same_frozen_identity_accepted',s.bind_frozen_inputs(current,sealed)==current)
    for key,value in (('date','2030-01-01'),('path','/artificial-only/drift'),('expected_rows',124),('expected_sha256','b'*64)):
        changed=copy.deepcopy(current);changed[0][key]=value;rejected=False
        try:s.bind_frozen_inputs(changed,sealed)
        except RuntimeError:rejected=True
        check('reject_current_'+key+'_drift',rejected)
    changed=copy.deepcopy(sealed);changed[0]['actual_sha256']='b'*64;rejected=False
    try:s.bind_frozen_inputs(current,changed)
    except RuntimeError:rejected=True
    check('reject_sealed_actual_hash_inconsistent',rejected)
    # Both live receipt and file's nominal identity may drift together: still reject vs frozen.
    changed=copy.deepcopy(current);changed[0]['expected_sha256']='b'*64;changed[0]['expected_rows']=999;rejected=False
    try:s.bind_frozen_inputs(changed,sealed)
    except RuntimeError:rejected=True
    check('joint_mutable_identity_drift_rejected',rejected)
    original_out=s.OUT;original_budget=s.Budget;original_argv=list(sys.argv)
    isolated=s.OWNER/f'synthetic-formal-budget-{s.time.time_ns()}'
    def failing_budget(phase):raise RuntimeError('SYNTHETIC_BUDGET_INITIALIZATION_FAILURE')
    try:
        s.OUT=isolated;s.Budget=failing_budget;sys.argv=[str(p),'formal'];caught=False
        try:s.main()
        except RuntimeError as exc:caught=str(exc)=='SYNTHETIC_BUDGET_INITIALIZATION_FAILURE'
        stop=isolated/'terminal-stop.json';content=stop.read_bytes()
        check('init_failure_is_terminal_in_isolated_out',caught and s.json.loads(content)['status']=='TERMINAL_FORMAL_FAILURE')
        check('init_failure_no_formal_started',not (isolated/'formal-started.json').exists())
        caught=False
        try:s.main()
        except RuntimeError as exc:caught='Existing terminal STOP' in str(exc)
        check('first_stop_preserved_and_restart_refused',caught and stop.read_bytes()==content)
    finally:s.OUT=original_out;s.Budget=original_budget;sys.argv=original_argv
    check('real_stage0_not_polluted',not (s.OUT/'terminal-stop.json').exists() and not (s.OUT/'formal-started.json').exists())
    result={'status':'PASS','utc':s.utc(),'scope':'only two preformal must_fix boundaries; original 18 economic/time fixtures reused, arithmetic/parser unchanged',
            'checks':checks,'check_count':len(checks),'implementation_sha256':s.sha(p),'tests_sha256':s.sha(__file__),
            'real_inputs_opened':0,'real_economics':0,'isolated_stop_fixture':str(isolated/'terminal-stop.json')}
    s.write_new(s.OWNER/'synthetic-tests-amended.json',result);rec=budget.finish('PASS');print(s.json.dumps({'tests':result,'resource':rec}),flush=True)
except BaseException:
    try:budget.finish('FAIL')
    except BaseException:pass
    raise
