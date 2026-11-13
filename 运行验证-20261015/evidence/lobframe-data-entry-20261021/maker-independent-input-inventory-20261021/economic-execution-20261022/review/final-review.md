# 唯一正式离线经济单元：独立终态验收

审阅UTC：2026-10-22 10:39:09。结论：**ACCEPTED_WITH_LIMITS；must_fix=[]**。接受的是一次已结束执行及其不可判定结论，不是经济候选通过。actual model/effort/speed UNKNOWN。

**当前配置应停止，不重跑、不调填单/窗口/费用以补成正结果。** 本轮没有建立完整可识别经济路径：8个比较全部UNKNOWN，16条F/H路径全部UNKNOWN。既不能把这视作赚钱，也不能把条件子路径负数当作完整策略亏损或所有过滤无效。若未来改变缺口处理或深度定义，应是明确新范围；本验收不启动它。

## 实际审阅与独立账式覆盖

已读result.json的状态/全部8格比较、两日summary的全部16条路径及计数/未知原因，formal-started/completion、Root formal-release、formal-exit-receipt、resource-formal、Owner report全文、terminal-seal及final-manifest。未读新行情源、权重或新标签，未重跑原回放/状态机/风险估值。

按照原完整验收允许的最小账式检查，独立标准库脚本`review/audit_saved_ledger.py`只读取两份已保存ledger和summary，未import执行Owner代码。已流式检查**全部**2,321,987条CSV记录：May1 1,213,205行，June1 1,108,782行；包括全部4,374条fill（May1 1,373、June1 3,001）及16条terminal_complete。不是抽样。

- 全部fill按日志的qty/price核fee=qty×price×费率；maker .003，terminal .004。逐行核cash变化=−带符号成交量×价−费用、BTC变化=带符号成交量、累计费用变化=本腿费用；非fill行余额不得改变。
- 16条终端记录BTC与全部预留归零，最终cash/BTC/fees逐路径等于summary，fill数等于summary；保存现金−5000等于已保存字段。没有生成新策略收益或重算风险。
- 已实际读取账本header，读过输出的小见证（各路径首/末成交、全部终端记录），程序覆盖所有fill但没有把数千行逐条人工读作另一份撮合审计。完整流式账式覆盖与人工见证范围明确区分。
- 结果为`PASS_SAVED_ACCOUNTING_ONLY`，原件`review/saved-ledger-audit.json`保存分母、各路径fill数、首/末见证、全部终端见证及全部fill字段摘要hash。这只证明已保存分支的账式自洽，不证明fill可得、未知分支无影响、真实队列或正确全风险。

另只作文件身份核对：`review/terminal-file-identity.json`核final-manifest中的16份必要原件（两ledger、两summary、result、5个代码/spec、seal、start/completion、stdout/stderr及exit receipt），实际bytes/hash均匹配。result SHA256 `fde97a75a504c1f20b167574759156b15df372ab53143ff5e96e9a3e7214ad67`；May账本 `7b4120954ff5faf469004bc122ac8b1c31964a31e8764bf4704abf00bd1de364`，June账本 `bc3d21407829e95032d903154fa44ed8c284b6824d561fc0069a5e647c0fb6ba`。源代码身份与已审7190a66d封存一致，没有正式后修复。

## UNKNOWN没有被清零或美化

两日每条路径均保留32,445个决策网格。接受价超出25档的队前量不明事件在账中明确为`UNKNOWN_queue_outside25`（May跨8条平行路径322次、June662次；不是现实独立订单的总数）。冻结实现对该未知新单不继续模拟其未来fill，因此终端cash可计算也只是条件子路径，后续库存/可报价可能不同，不能称完整政策PnL。

16条路径均有持仓风险参考缺失计数，不能把局部最大库存/回撤当完整风险。所有归因也为UNKNOWN；不把现金差归为报价收入、避免不利成交或库存上涨。result的8格risk比较均null、status均UNKNOWN；尽管F保存现金差8格全负、Δ有正负，最终仍`UNKNOWN_NOT_ECONOMICALLY_IDENTIFIED`。Owner报告明确上述限定，未将未知当负、未删除不利情景、未升级为真实盈利。

账式检查未重做队前量、source guard、参考时效或风险，这些沿已完成静态代码审阅及封存输入QC的有限证据；BTC单位、名义时钟/延迟、无冲击等仍是模型条件，个人获单、费用权益及外生成本未认证。

## 唯一执行及资源

Root release绑定seal `7190a66de5030fa63514f6bac0266b959692d49fcce926daef2cfd9eecc19b07`。实际start与completion同PID32610，UTC10:35:36.439637至10:36:34.944252；退出回执记录session12439/exit0/no_retry，stderr为空，正式marker保留。可核证据支持一次正式，未发现重启；不把文件回执说成本人独立OS历史进程穷举。

正式记录CPU55.352344秒、wall58.522152秒、峰RSS83,525,632字节、单线程、Owner输出25,741,653字节（记录时点）。准备四次累计CPU .196066，Owner脚本累计55.548410；另文件封存记录 .026885秒。原整单600CPU秒/512MiB/64MiB/12:11:26截止不变，60秒审阅保守借记不能冒充实测或再加一份新帽。

本次独立账式脚本实测CPU10.193612秒、wall10.427888秒、峰RSS12,550,144字节；文件身份辅助CPU .013688秒，均在既定60秒借记及本次≤35秒小检查范围内。新增仅review内脚本、小回执及本审阅，未写Owner或原输入；没有新数据/网络/安装/模型/账户/交易。数值不声称覆盖每条平台工具调用的精确OS成本。原实验/旧STOP及终态保持，不自动延续。

## 定点解释补充：outside25不等于必须新增深度数据

补读core.py L129–136确认：post-only检查后，`min(side25prices)<=ownL<=max(side25prices)`才允许初始化队列，因此价差内部的改善报价也会被记outside25；这类报价不在同侧已显示价位范围，却不等于位于更深不可见盘口。在同快照/无隐藏量的模型假设下，价差内部可见队前量可定义为0，不必先取得更深L2/L3。当前代码及spec的outside25 UNKNOWN规则已在正式前冻结；相对于原文“可见范围内无该价可设a=0”，它采用更窄的同侧报价区间作为实现域，属于预先冻结的模型域/实现限制，不能把日志名称本身当作客观数据不足证明；原协议没有明确指定价差内部的队列分支，不能据这一处静态事实断言已违反一个明示分支。

本审阅未逐事件读取接受时book，**不认定实际outside25事件全部或任何特定比例属于改善报价**，也不改旧分类、补成交或重跑。前文“不能给当时该挂价队前量”的表述应严格理解为当前冻结实现没有给出队前量，而不是所有情形数学上无法用现有输入定义。根结论不能据此要求所有UNKNOWN都必须靠新增数据解决。该解释不影响接受已结束UNKNOWN终态，也不改变停止当前配置、不放宽门槛/重跑的意见。
