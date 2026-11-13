"""Metadata-only check of formal startup guard; no inputs/GET/labels."""
import run
from core import *
budget=Budget('runtime-binding-check');checks=[]
try:
 actual={'executable':run.sys.executable,'version':run.sys.version}
 run.validate_runtime(actual);checks.append('actual_preflight_interpreter_accepted')
 for label,change in [('wrong_executable',{'executable':'/synthetic/other-python'}),('legacy_writer3.9_rejected',{'version':'3.9.6'})]:
  failed=False
  try:run.validate_runtime({**actual,**change})
  except RuntimeError:failed=True
  if not failed:raise AssertionError(label)
  checks.append(label)
 pre=json.loads((OWNER/'preflight.json').read_text())
 if actual['version']!=pre['Python']:raise AssertionError('Actual preflight version mismatch')
 checks.append('actual_version_matches_original_preflight')
 write_new(OWNER/'runtime-binding-check.json',{'status':'PASS','utc':now(),'checks':checks,'actual_runtime':actual,'guarded_runner_sha256':sha(OWNER/'run.py'),'real_inputs_opened':0,'GETs':0,'labels':0})
 print(json.dumps(budget.finish('PASS')))
except BaseException:
 try:budget.finish('FAIL')
 except BaseException:pass
 raise
