# 独立库存退出：准备完成，正式未开始

实现入口run.py，唯一路径`formal`；尚未启动或读取历史行情正文。32项人工合成通过。新core.py显式继承逐字保存的base_core.py；inputs.py与原纠错版逐字一致，prepare有实际hash guard。旧F0/H0只引用旧result，不重跑。完整差异complete-diff.patch；规范与版本来源spec.json；输入小身份/runtime/源与合成绑定preparation-seal.json。

新增实现：每buy fill FIFO lot，统一sell扣减；年龄1秒触发→撤两侧屏障δ→固定FIFO退出量及独立预留→再δ到达。退出锁期原grid/sign照记仅阻新提交；Q0于τ解锁且严格后继整秒恢复。退出同capture组共用有限25档预算，新capture组才重置；年龄/日终共同扣。已发送exit不被日终取消，未发屏障由终端接管。路径参考/深度不可识别则保留首UNKNOWN、现金/BTC/预留并冻结该路径；其他预定路径照报。完整现金/风险/归因分层；有BTC且风险参考已被exit消费则价格风险UNKNOWN；纯现金仍可知。新增增量日志含FIFO分配/lot余量、事务/发送冻结量及预留、深度reset及before-used-after、终端接管/阻断/UNKNOWN。

合成覆盖见synthetic-receipt.json逐项32 PASS：FIFO部分买卖、<q、两段延迟、发送后成熟下一批、冻结量、预留、Q0、缺参考/不足全量不部分执行、同组累计/新组重置、消费后风险、pending冲突取消、终端sent/unsent接管、不双卖、锁期grid/sign与日志证据。人工报价fixture原只有0时点，首轮因年龄>1s变陈旧而失败；原失败log/resource和旧tests均保留，修为人工0.5s更新序列后通过，没有历史结果择参。第二代进一步加边界的原源/receipt/seal保留history-prepare-v1及prior-v1文件，原资源没有复制进历史重复记账。

当前Python固定绝对解释器/3.12.14实际回执见synthetic/preparation-seal；正式也强校验同executable/version。32项全部是人工，无真实行情预演。准备CPU各resource按实测累计，另resource-auxiliary-debit对短小文本编辑/hash进程保守扣1CPU秒（不冒称实测），Root/Reviewer另预留150s；Owner上限450CPU，总600。线程1、RSS512MiB，Owner磁盘guard120MiB预留共享8MiB，截止16:01:37UTC；无付费/网络/数据/下载安装/模型/账户钱包交易。actual model/effort/speed UNKNOWN。

唯一formal须Root `RELEASED_ONE_FORMAL_ECONOMIC_UNIT`绑定当前seal且原件身份一致；排他formal-started先写，技术失败/超帽首STOP不重跑。仅必要适配及预正式合成已执行，正式、未来新规则与择优运行未执行。当前等待独立静态审阅及Root版本放行。

## 预正式独审整改

唯一must_fix已落实：接受时真正更深outside25的首执行UNKNOWN现在保留原订单/预留/现金/FIFO，立即冻结该路径，不再继续maker/age/grid；risk_unknown单独不冻结。base_core和inputs仍逐字原样。新增深档人工fixture及冻结不推进检查，当前35项合成PASS（原32项亦随同准备入口复验，无历史body）。修前源/seal/receipt/diff完整留history-pre-review-74528c及prior-74528c，所有resource留原位无重复记账。局部unknown-freeze-fix.diff与当前完整diff/ready/seal同步；正式从未开始。

补充同一freeze闭合：冻结路径risk_status强制UNKNOWN，BTC秒与风险数值保留但明确KNOWN_PREFIX，不冒称全窗完整；compare无法把冻结双方风险判完整。36人工合成PASS，其中新增冻结前无风险缺口的prefix状态检查。所有历史版本与资源保留，未正式。

# 正式终态：固定库存退出版本未通过经济必要条件
唯一正式进程exit0；只运行新F1/H1，F0/H0均为原封存引用。两日仍为原共同前缀00:00:05–09:00:49，非整24小时、非新OOS。7格新现金完整、F1净额均负；June X500两臂首退出参考缺失后冻结，其净额UNKNOWN。不把未知算亏损或算通过。停止这个固定1秒触发/两段延迟退出版本晋级，不自动试新持有期或费用。
|日期|情景|F0净额|H0净额|F1净额|H1净额|F1−H1|F1−F0|H1−H0|新风险比较|
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
|2026-05-01|E100|-3.0678|-2.8618|-5.3754|-6.6050|1.2296|-2.3076|-3.7433|完整且F1≤H1|
|2026-05-01|E500|-4.6006|-3.9453|-8.3395|-8.2376|-0.1019|-3.7389|-4.2922|完整但F1≤H1未过|
|2026-05-01|X100|-33.8095|-34.8474|-44.3463|-44.0726|-0.2737|-10.5368|-9.2252|UNKNOWN|
|2026-05-01|X500|-42.2043|-43.3238|-51.5990|-53.7520|2.1530|-9.3947|-10.4282|UNKNOWN|
|2026-06-01|E100|-6.4736|-5.2990|-5.0709|-5.0831|0.0122|1.4027|0.2159|完整且F1≤H1|
|2026-06-01|E500|-5.3644|-4.1094|-4.7286|-3.7692|-0.9593|0.6358|0.3401|完整但F1≤H1未过|
|2026-06-01|X100|-97.4048|-88.6693|-108.6610|-105.5296|-3.1313|-11.2562|-16.8603|UNKNOWN|
|2026-06-01|X500|-114.9546|-118.2122|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|

全部金额USD，表仅四位展示；result.json保持原精确Decimal。June E两格F1较F0少亏，但新净额仍负；其他现金完整格F1更差。新旧现金差是完整政策变化，包含资金/入场资格/成交构成，不能称相同成交的纯退出alpha。旧新同风险比较仍UNKNOWN，旧价格风险不被补造。

## 费用与状态逐路径

|日期|情景|臂|总fee|maker fee|年龄taker fee|日终taker fee|BTC秒范围|
|---|---|---|---:|---:|---:|---:|---|
|2026-05-01|E100|F1|5.2426|2.2470|2.9955|0.0000|FULL_SIMULATED_WINDOW|
|2026-05-01|E100|H1|6.4293|2.7557|3.6736|0.0000|FULL_SIMULATED_WINDOW|
|2026-05-01|E500|F1|8.0662|3.4574|4.6088|0.0000|FULL_SIMULATED_WINDOW|
|2026-05-01|E500|H1|7.9369|3.4020|4.5348|0.0000|FULL_SIMULATED_WINDOW|
|2026-05-01|X100|F1|42.8677|18.3744|24.4933|0.0000|FULL_SIMULATED_WINDOW|
|2026-05-01|X100|H1|42.5828|18.2523|24.3305|0.0000|FULL_SIMULATED_WINDOW|
|2026-05-01|X500|F1|49.7874|21.3406|28.4468|0.0000|FULL_SIMULATED_WINDOW|
|2026-05-01|X500|H1|51.8252|22.2141|29.6111|0.0000|FULL_SIMULATED_WINDOW|
|2026-06-01|E100|F1|4.8838|2.0934|2.7904|0.0000|FULL_SIMULATED_WINDOW|
|2026-06-01|E100|H1|4.8895|2.0958|2.7937|0.0000|FULL_SIMULATED_WINDOW|
|2026-06-01|E500|F1|4.5442|1.9478|2.5963|0.0000|FULL_SIMULATED_WINDOW|
|2026-06-01|E500|H1|3.6104|1.5476|2.0628|0.0000|FULL_SIMULATED_WINDOW|
|2026-06-01|X100|F1|104.8522|45.8768|58.9755|0.0000|FULL_SIMULATED_WINDOW|
|2026-06-01|X100|H1|101.6842|44.0682|57.6159|0.0000|FULL_SIMULATED_WINDOW|
|2026-06-01|X500|F1|55.0672|23.6449|31.4223|0.0000|KNOWN_PREFIX_ONLY|
|2026-06-01|X500|H1|55.7929|23.9559|31.8370|0.0000|KNOWN_PREFIX_ONLY|

maker分项是已保存总fee减年龄/日终分项的会计恒等式，无费率扫描。age/terminal notional及原计数、现金/BTC/风险完整性见result与两日summary。全部非冻结路径日终BTC已清零且没有剩余日终taker成交；这说明该模型的出清路径变了，不能据此把省下的日终费再加一次，或认定收益提高。

## 两条不可识别路径与风险限制

2026-06-01 X500 F1：首UNKNOWN=[[17802852063633354, "age_exit_reference_missing"]]；保留BTC=0.000323370000、exit_reserved_BTC=0.00032337、phase=flight；PnL=null。BTC秒和局部风险只为冻结前已知前缀，不当全窗值。未读取后继报价挽救退出。

2026-06-01 X500 H1：首UNKNOWN=[[17802852063633354, "age_exit_reference_missing"]]；保留BTC=0.000323370000、exit_reserved_BTC=0.00032337、phase=flight；PnL=null。BTC秒和局部风险只为冻结前已知前缀，不当全窗值。未读取后继报价挽救退出。

E100两日新F/H三风险完整且F1≤H1，但净额负；E500两日风险完整但F1≤H1不满足。X风险按各路径原始缺参考或已消费snapshot fullbook不可认证等原因保留UNKNOWN；局部max不能充完整风险。具体first_risk_unknown/risk_unknown_count在每path。总体已有明确现金必要失败，不因其他未知改成通过。

本结果只约束既定费用/信号/报价/时钟/队列/单位假设和这两日窗口。真实本人获单、真实路由/冲击/个人费用、容量和样本外优势未认证；不作实际ROI或盈利承诺。原D及所有旧STOP保持。

## 实际执行与资源

UTC14:22:50.008470–14:23:50.914911；PID88229、工具session70872、启动chunkc0ca1a、结束poll chunkcfaf3e、exit0，stderr为空。正式CPU59.873906s、wall60.924128s、峰RSS113016832B；原prepare实际+辅助保守借记1.252920s，正式后累计Owner61.126826s，另150s为review/Root预算预留而非实测，合计211.126826s。文件级报告/哈希的额外微小实际CPU另见resource-final-files.json。正式完成时输出16845529B，远低共享128MiB。无新网络/数据/下载/安装/付费/模型/账户钱包交易。actual model/effort/speed UNKNOWN。

原始stdout/stderr、两日完整压缩ledger、16path/8comparison结果、准备历史、source/diff/spec/seal、formal启动/完成/resource/实际exit均保留；未再次执行策略或扫描市场。最终原件身份见final-manifest.json与terminal-seal.json，独立账验另由review负责。
