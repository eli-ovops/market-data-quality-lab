"""Saved-result reporting and file-level seals only; no strategy/market imports."""
from pathlib import Path
import json,hashlib,time,resource,datetime,os
from decimal import Decimal
p=Path(__file__).resolve().parent;start=time.process_time();now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):
 with (p/n).open('x') as f:json.dump(x,f,ensure_ascii=True,indent=2);f.write('\n')
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as x:
  for chunk in iter(lambda:x.read(65536),b''):h.update(chunk)
 return h.hexdigest()
def show(x):return 'UNKNOWN' if x is None else format(Decimal(x),'.4f')
r=json.loads((p/'result.json').read_text());rs=[json.loads(f.read_text()) for f in p.glob('resource-*.json')];formal=next(x for x in rs if x.get('phase')=='formal')
lines=['\n# 正式终态：固定库存退出版本未通过经济必要条件\n','唯一正式进程exit0；只运行新F1/H1，F0/H0均为原封存引用。两日仍为原共同前缀00:00:05–09:00:49，非整24小时、非新OOS。7格新现金完整、F1净额均负；June X500两臂首退出参考缺失后冻结，其净额UNKNOWN。不把未知算亏损或算通过。停止这个固定1秒触发/两段延迟退出版本晋级，不自动试新持有期或费用。\n','|日期|情景|F0净额|H0净额|F1净额|H1净额|F1−H1|F1−F0|H1−H0|新风险比较|\n|---|---|---:|---:|---:|---:|---:|---:|---:|---|\n']
for c in r['comparisons']:
 risk='UNKNOWN' if not c['risk_complete_both'] else ('完整且F1≤H1' if c['risk_comparable_and_F_not_higher'] else '完整但F1≤H1未过')
 lines.append('|'+c['day']+'|'+c['model']+str(c['delay_ms'])+'|'+'|'.join(show(c[k]) for k in ('F0_PnL_USD','H0_PnL_USD','F_PnL_USD','H_PnL_USD','delta_F_minus_H_USD','F1_minus_F0_USD','H1_minus_H0_USD'))+'|'+risk+'|\n')
lines+=['\n全部金额USD，表仅四位展示；result.json保持原精确Decimal。June E两格F1较F0少亏，但新净额仍负；其他现金完整格F1更差。新旧现金差是完整政策变化，包含资金/入场资格/成交构成，不能称相同成交的纯退出alpha。旧新同风险比较仍UNKNOWN，旧价格风险不被补造。\n','\n## 费用与状态逐路径\n\n|日期|情景|臂|总fee|maker fee|年龄taker fee|日终taker fee|BTC秒范围|\n|---|---|---|---:|---:|---:|---:|---|\n']
for x in r['path_results']:
 maker=Decimal(x['fees_USD'])-Decimal(x['age_exit_fees'])-Decimal(x['terminal_fees'])
 lines.append('|'+x['day']+'|'+x['model']+str(x['delay_ms'])+'|'+x['policy']+'|'+show(x['fees_USD'])+'|'+show(str(maker))+'|'+show(x['age_exit_fees'])+'|'+show(x['terminal_fees'])+'|'+x['inventory_time_scope']+'|\n')
lines+=['\nmaker分项是已保存总fee减年龄/日终分项的会计恒等式，无费率扫描。age/terminal notional及原计数、现金/BTC/风险完整性见result与两日summary。全部非冻结路径日终BTC已清零且没有剩余日终taker成交；这说明该模型的出清路径变了，不能据此把省下的日终费再加一次，或认定收益提高。\n','\n## 两条不可识别路径与风险限制\n']
for x in r['path_results']:
 if x['frozen']:lines.append('\n'+x['day']+' '+x['model']+str(x['delay_ms'])+' '+x['policy']+'：首UNKNOWN='+json.dumps(x['unknown'])+'；保留BTC='+x['BTC']+'、exit_reserved_BTC='+x['exit_reserved_BTC']+'、phase='+x['age_phase']+'；PnL=null。BTC秒和局部风险只为冻结前已知前缀，不当全窗值。未读取后继报价挽救退出。\n')
lines+=['\nE100两日新F/H三风险完整且F1≤H1，但净额负；E500两日风险完整但F1≤H1不满足。X风险按各路径原始缺参考或已消费snapshot fullbook不可认证等原因保留UNKNOWN；局部max不能充完整风险。具体first_risk_unknown/risk_unknown_count在每path。总体已有明确现金必要失败，不因其他未知改成通过。\n','\n本结果只约束既定费用/信号/报价/时钟/队列/单位假设和这两日窗口。真实本人获单、真实路由/冲击/个人费用、容量和样本外优势未认证；不作实际ROI或盈利承诺。原D及所有旧STOP保持。\n','\n## 实际执行与资源\n','\nUTC14:22:50.008470–14:23:50.914911；PID88229、工具session70872、启动chunkc0ca1a、结束poll chunkcfaf3e、exit0，stderr为空。正式CPU59.873906s、wall60.924128s、峰RSS113016832B；原prepare实际+辅助保守借记1.252920s，正式后累计Owner61.126826s，另150s为review/Root预算预留而非实测，合计211.126826s。文件级报告/哈希的额外微小实际CPU另见resource-final-files.json。正式完成时输出16845529B，远低共享128MiB。无新网络/数据/下载/安装/付费/模型/账户钱包交易。actual model/effort/speed UNKNOWN。\n','\n原始stdout/stderr、两日完整压缩ledger、16path/8comparison结果、准备历史、source/diff/spec/seal、formal启动/完成/resource/实际exit均保留；未再次执行策略或扫描市场。最终原件身份见final-manifest.json与terminal-seal.json，独立账验另由review负责。\n']
with (p/'report.md').open('a') as f:f.write(''.join(lines))
save('actual-exit-receipt.json',{'utc':now(),'formal_PID':88229,'tool_session_id':70872,'launch_chunk':'c0ca1a','final_poll_chunk':'cfaf3e','exit_code':0,'command':"exec env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 '/Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/.venv/bin/python' -B run.py formal > formal-stdout.log 2> formal-stderr.log",'cwd':str(p),'formal_runs':1,'no_retry':True})
files={}
for f in sorted(p.rglob('*')):
 if f.is_file() and f.name not in ('final-manifest.json','terminal-seal.json','resource-final-files.json'):files[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
save('final-manifest.json',{'utc':now(),'status':r['status'],'files':files,'source_seal_sha256':sha(p/'preparation-seal.json'),'scope':'F1H1 only 16paths; seven cash comparisons complete, one UNKNOWN; no old replay'})
save('terminal-seal.json',{'utc':now(),'status':r['status'],'final_manifest_sha256':sha(p/'final-manifest.json'),'result_sha256':sha(p/'result.json'),'report_sha256':sha(p/'report.md'),'actual_exit_receipt_sha256':sha(p/'actual-exit-receipt.json'),'formal_exit_code':0,'further_strategy_execution':'STOP_FIXED_VERSION_NOT_PROMOTED'})
cpu=time.process_time()-start
save('resource-final-files.json',{'utc':now(),'phase':'final_file_seal','CPU_seconds':cpu,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'output_bytes':sum(f.stat().st_size for f in p.rglob('*') if f.is_file()),'method':'saved scalar reporting plus file hashes; no replay or market read','prior_Owner_CPU_debit':sum(x['CPU_seconds'] for x in rs),'cumulative_Owner_CPU_debit':sum(x['CPU_seconds'] for x in rs)+cpu,'review_Root_budget_reserve_not_measured':150})
for n in ('result.json','report.md','final-manifest.json','terminal-seal.json'):print(n,sha(p/n))
print('file_seal_CPU',cpu)
