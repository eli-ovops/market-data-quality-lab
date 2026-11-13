# 扣费前亏损：会计恒等式、参考时序与信号边界

结论：可把已保存净现金机械拆成费用、库存记账价格变化、相对记账mid的成交价项；**不能把后两项分别命名为“信号损失”和“真实价差/冲击成本”**。固定1bp项可单独识别同一保存成交路径上的机械价差，但加回它不是新策略。唯一建议是**停止当前固定执行版本的经济晋级**，完成本次已授权会计拆账与验收后收口；不靠更改方向/周期或挑毛差为正格继续。原D信息证据保留，不由本账否证所有成交流信号。

本轮只静态读本新owner冻结core/base_core/run/inputs及result/已有小报告，不读大账或行情、不import或执行引擎；Data Owner负责唯一账归纳。以下行号均指inventory-exit-minimal-plan-20261022/execution-20261022/owner/，源码/result身份见source-receipt.json。actual model/effort/speed UNKNOWN；旧源/结果/STOP不改。

## 1. 账如何更新：等式可核，mid不是无条件同期可执行价

令库存I、现金K、记账mid m、成交带符号量dq（买正卖负）、成交价p、显式费f。

- observe(t)：先tick计算已有库存的BTC秒；有book才取m_new=(best ask+best bid)/2，以**更新前的现存库存**记 `V += I*(m_new−m_old)`，然后把m改为m_new（core35–43）。同刻无新mid变化再observe，V增量0。缺book时m不被清空；若当时I>0则永久置attr_unknown。m本身是保存报价的中点，不是可保证成交价格。
- fill：普通maker在更新成交前observe；记 `K -= dq*p+f`、`I += dq`，并记 `X += dq*(m−p)`、`C += f`，随后写fill日志，再普通maker成交后observe（core100–124）。FIFO只分配库存身份，不改变这些价款等式。年龄退出先用有效book做一次observe，再逐腿fill(risk_observe=False)，全部腿后observe；各腿共用该次记账mid，不在腿间重造book（157–179）。
- 有完整归因且首末BTC=0时，保存的恒等式为 `N=K_final−5000=V+X−C`，故 `G=N+C=V+X`；base_core209–216仅在attr_unknown=False且最终清仓成立才给attribution，并强制精确残差0。这是自融资账按选择的mid过程做分解，不是因果识别。

**日志mid的有效性。** run42–47只把e.m原样写入mid_reference，没有“本次fresh成功”字段。observe缺book不会清m，所以某个fill的日志mid**可能沿用较早值**，不能见到非空就称该时刻fresh/可执行参考。maker fill前后observe意味着：缺参考且成交后持BTC会置attr_unknown；有BTC的卖成交前缺参考也会置未知。因而全路径attribution完整是额外的口径约束，不能由一般可沿用机制反推所有完整路径的fill都陈旧。即使ref成功，也只是capture/source严格在先、capture年龄≤1秒（inputs42–45）的最近记录，不是“同一撮合瞬间”报价，更不是用户到所钟。

**为何risk UNKNOWN而归因可有值。** core39–42先更新mid/V，随后48–51可因该snapshot已被exit消费或完整深度不足把价格风险记UNKNOWN；这两类并不自动置attr_unknown。中点仍可记账，fullbook却不能认证可执行变现风险，二者职责不同。不能用归因精确闭合洗掉risk UNKNOWN，也不能用risk UNKNOWN抹掉独立完整现金。

**明确缺口。** 保存result中May X500 H1的cash完整，但attribution=None；其first_risk_unknown包括reference_unavailable，且core43会令全路径归因未知。F1有完整分项不能替代H1。可核H1的G=N+C、费用及机械1bp项，但不能拿H1累计的部分V/X冒称全路径拆解，也不能据此形成完整ΔV/ΔX或“差额全来自某项”。June X500两条冻结路径连全窗N/G都未知，只能报告已知前缀，禁止补全。

## 2. 固定1bp能从保存notional分出什么

s=.0001，年龄/终端每档卖价为 `p_i=b_i*(1−s)`（core143–156，尤其153；base_core25–37是原估值/清算公式）。对已保存该腿量q_i：

`S_i = q_i*b_i*s = actual_exit_notional_i*s/(1−s)`。

S≥0是同数量、同被选bid档、同一次保存成交上的**显式1bp不利价格金额**。没有把费用重复计入；maker不施加此项，taker .004按已经不利后的actual notional另扣（core104–114）。若保留完整腿，sum(S_i)可直接机械复核；只要退出notional已保存，同类总notional亦可做同一线性换算。

对卖腿，执行项 `dq*(m−p)=q*(p−m)=q*(b_i−m)−S_i`。于是加回S后剩下的成交项仍混合mid到该bid档的报价差/所用深度、等待期间价格变化、成交选择和m口径；V亦取决于入场/退出及库存路径。不能把全部X叫真实spread，不能把S叫实测市场冲击，也不能凭notional反推出best-bid到深档的独立成本（需要当时各参考价的有效对应）。新组重置、无冲击与队列规则本身均是条件假设。

`G+S`只能叫保存路径加回固定模型价差的会计金额，不是“零滑点策略收益”；真实取消/到所、冲击、隐藏量/本人容量未知。移除该项若重跑会改变现金、预留和后续路径，本轮没有这种运行。数据归纳若将fill.mid用于分组，应称“相对保存记账mid的成交项”，而不是未经验证的同期fresh markout。

## 3. 原D、F/H毛差与实际成交人口不相同

原F在主动买多数时暂停sell、主动卖多数时暂停buy（base_core219–224）；信号仅过去1秒已收trade笔数（inputs109–116）。但现货BTC0不能从空仓卖，普通sell需至少q的已持可用BTC（base_core88–94）；买入后年龄退出锁两侧、两段δ、固定FIFO发量，锁定期仍记grid/sign但阻新提交（core59–62、131–196）。F/H不同成交随后改变现金、可报价和库存，不能事后按成交量配平。

因此原D的实际被动ID/参考资格/网格方向等权人口，与新虚拟maker买/卖及年龄taker的成交集合不同。原D含双侧标签差，不是“这条仅可先买的实际路径每次赚D”；1秒标签时点也不等于买fill+1秒触发+2δ退出。D正不能保证两套人口的gross差或收益。

如果Data得到多个格 `G_F−G_H>0`：它只说明该格保存F完整政策的毛现金相对H更好，绝不自动意味着F绝对G>0/N>0。美元毛差还受买入名义、成交数与构成、FIFO库存、退出和风险影响；不能当配对信号收益或显著胜率。统一买入名义的比率可描述每美元输入的保存结果，但也不能消除成交选择/风险或变成随机对照。八格是同两日的模型情景，不是八次独立实证。

**收口。** 当前已知七格F1完整N均负，部分风险完整/部分未知，另格冻结；本只读会计分解可定位已记金额，却没有识别“如果换方向/周期/成交就能赚”的因果证据。停止此固定政策晋级；保留D描述性信号与执行失败为不同层，不外推XTX私有机制，不自动开启新实验。

资源与来源：仅小文件静态读取、数学恒等式说明及来源hash；无金融重放/新价格标签/策略/模型/网络/安装/付款/账户交易。一次小来源封存的CPU/RSS见source-receipt.json；本输出不改任何旧封存。
