# 输入reader验收清单（实际源码尚未就绪）

状态：**PENDING_ACTUAL_READER，不是PASS。** 本轮目录清单时economic-execution-20261022只有root/review，未有Owner reader代码；不审空壳或用旧QC替新实现背书。当前只固定以下独立来源/QC验收项，等同一Owner实际代码与合成回执就绪后按行号审阅。

已读root/authorization.json：本次用户直接“继续”授权四情景完整离线单元，计划SHA原717faa14…1b089及v2 e1e14f8…adba1；UTC10:11:26–12:11:26、累计CPU/计算600秒、RSS512MiB/新增输出64MiB，0新行情/安装/付费。源码适配/执行Owner为lobframe_label_timing；本Reviewer不运行程序、不读大行情或再跑QC。

## 固定reader检查项

1. 固定May1/Jun1、暖机00:00起至09:00:52含端点；决策00:00:05–09:00:49，最后片540。固定输入路径只落已封存项目缓存，不跟symlink到保护Library/新来源；不改窗救结果。
2. 绑定旧GET账、两日data-seal、snapshot data-receipt以及本次输入QC metadata身份。raw来源必须是已存数量原件，而非无amount的normalized。大BBO身份沿现有封存/Owner必要检查，本Reviewer不重hash。
3. 七位UTC capture→整数100ns，不先由datetime/浮点截到µs；source_microtimestamp整数µs→100ns仅乘10一次。snapshot local/source同为epochµs→100ns。原实际成交source全在1000µs格、snapshot值格1µs，不认证真实准确度。
4. price/amount优先字符串，Decimal精确解析；fallback数值应避免先过binary float损失。核有限、价>0、量>=0（trade量>0），双编码矛盾/身份缺失按固定输入失败；禁止统一设每笔1量。BTC为继承的显式模型单位假设，不把本reader叫官方认证。
5. 原tradeID去重/冲突停；0/1方向映射、双订单ID仅追溯，不能作为自己的订单或前视字段。trade同capture归组不得顺序择好；归组在reader或上层须有唯一职责且保留供源序guard使用的信息。
6. snapshot所有25×两侧价量100字段完整且有序；同capture必须合并为组，任一数值冲突保留该组无效，不能取“最后较好行”覆盖。若只读top1会漏同戳深层差异，须与终端25档职责一致。
7. strict-as-of选择先按capture找最后组，再判capture/source严格早于检查点、年龄≤1s、冲突/源序等；不跨过较新无效组回退到较旧“好”报价，不取未来最近行。名义代表点是固定模型规则，不复用旧±误差区间偷偷改模型。
8. 明确断流/未知不可用新行补为过去可知；前缀已有两日各1个同capture冲突组及若干>1s参考，静态reader不能假定全部检查点有效。新经济状态机怎样暂停/取消另由经济Reviewer审，来源审只保证原始可用性标志不被抹掉。
9. 终端先查09:00:51 strict-as-of，若失效，仅至09:00:52按时间取首个完整参考；抵达时可用（该观察允许capture等于观察时刻），不看价格挑择，不延长，不预先硬编码已知答案。已QC见证：May首51.7286490/source51.700864，Jun51时点可用50.9196430/source50.891157。存在参考不等于模型库存扫档足够；深度消费不在本reader验收中重复审。
10. p0及报价只来自截至当时已知参考；不得从以后print价/实际被动ID补自己报价。reader不得预过滤“未来会成交/有收益”的记录。source迟到guard的全历史prefix最大值须能由raw信息构造，不能只留过去1秒。
11. 合成原件须覆盖：七位尾数、µs→100ns、Decimal长小数/双编码冲突、同capture深层冲突、最新无效不回退、capture/source等于cutoff不合格、age恰1s与超1s、终端51无fresh但52内首可用/完全无可用、暖机/前缀边界。只审Owner合成输入与回执，不执行。
12. 实际代码/参数/输入metadata及合成结果须封存绑定；Reviewer结论必须注明已审版本与行号。未就绪不作release建议，正式运行结果也不自动证明reader正确。

## 本次复读依据

授权原件；next-validation-design/input-readonly-precheck/method-spec.json、FINDINGS.md、input-metadata-identities.json；原方案与v2相关输入/时序/终端条款。之前独立QC一次完成只证明当时缓存字段/参考可用性，不是当前经济reader实现测试。无新增网络、行情读取、源码执行、模型或交易；实际model/effort UNKNOWN。

保存UTC：2026-10-22T10:18:34.949766+00:00
