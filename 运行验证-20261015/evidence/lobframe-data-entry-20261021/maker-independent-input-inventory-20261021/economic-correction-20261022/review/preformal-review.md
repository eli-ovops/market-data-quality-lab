# 独立正式前代码与合成原件审阅

审阅UTC：2026-10-22 11:13:10。**READY_WITH_LIMITS；must_fix=[]**。本结论为冻结版本的静态/合成原件准备验收，Root仍须按授权生成release，未代为执行或放行formal。actual model/effort/speed UNKNOWN。

绑定preparation-seal SHA256 `fcc3295c53afb72181d4ce46bbed69c811bf5efe0a4af41b278eaa5130a88cbe`；版本核验详见本目录`version-binding.json`。实际代码、spec、合成回执与seal中hash一致，授权hash一致，seal的inputs对象与旧7190版逐字段相同。没有读取输入body或重新QC。

## 实质检查结论

1. **改善报价分支符合唯一修订范围。** core.py L125–140先取原有效严格参考并保持post-only检查，再仅对strict bid<L<ask设显示ahead=0；其他价格回原同侧可见范围/同价量计算。没有扩大到真正深档、穿过对手价或无参考报价。与原版完整diff仅此接受分支及结果分层变化；后续打印量、source guard、TTL/取消、费用/终端与守恒逻辑原样。该0是既定无隐藏量/无先插队的显示队列模型，不认证实际队首。

2. **现金必要失败不被风险UNKNOWN遮盖；正值仍无捷径晋级。** core.py L209–217以执行未知清单及terminal_done定义现金完整，risk_unknown独立，原归因可得时精确残差raise保留。L227–241先识别F/H现金完整性：Δ只在双方完整时计算；F完整且≤0立即现金必要失败；双方完整的Δ≤0也失败，均不依赖risk已知。F未知负值不会误认证失败。只有现金为正及增量为正、双方风险完整且三项F≤H才cell pass。归因UNKNOWN不额外阻挡候选，也不虚构归因0。run.py L97–109交付全部8比较/16path，整体现金失败优先，但保留execution/risk未知flag，不能据整体标签隐藏其他未知。

3. **继承规则及单次保护未静默改变。** inputs.py与已审原reader逐字相同（完整diff为空且hash一致），1秒freshness、source/冲突/严格as-of及Decimal精度拒绝规则不变。F/H信号、报价、两日窗口、四情景、现金/库存/预留、费用/滑点及原风险定义未改变。runner只增加compare调用及新截止/资源适配；release→seal→runtime/source/auth/input身份链与先写排他formal marker/首失败不重跑原保护保留。截止整数13:08:23比授权小数截止略严格，未放宽；旧150保守借记、新Owner390、新review/root60共享600CPU秒。

## 合成与运行原件

完整读complete-source.diff、report.md、全部47项synthetic-receipt，检查实际core改动与比较函数、run身份/汇总调用及测试新增实现。复用原代码已完整审阅的不变部分；新增测试与diff中逐项阅读。47项含双侧改善、best/空价/真正深部、穿对手拒绝、参考缺失、部分成交/穿价/取消及资金量守恒，另覆盖现金完整风险未知、F已知负而H未知、Δ不可算、F未知负不认失败、风险不齐不晋级及全条件合格边界；原33项中Decimal尾数、真实parser深层同capture冲突、多档终端原子风险及残差保护保留。回执报告47 PASS，不等于本Reviewer重跑。

实读prepare-completion、preparation-manifest、resource-prepare及文件封存resource。prepare PID48351、项目.venv Python3.12.14、exit0，CPU .063858秒/峰RSS30,064,640字节；另文件封存CPU .037903，记录新Owner累计 .101763秒，150旧借记及60新验收预留不冒充实测。Owner报告/manifest正式尚未开始，本Reviewer未运行prepare/formal或任何金融计算。

## 验收限制

- 这次仍为已见May/June上的纠错诊断；修复可判定性不是补上样本外/个人执行证据。新接受订单会改变全路径，不能往旧现金直接加fill。
- 路径risk值只有对应执行模型定义完整且risk_status完整时，才有完整政策比较含义；若执行层仍未知，即使局部风险参考都可得，也不能据该子路径风险认证完整策略。当前compare先要求现金完整，未发现由此错误晋级的路径。
- 原风险UNKNOWN可继续存在，不延长age/挑旧参考/清零库存。完整现金失败可独立成立；正现金遇风险UNKNOWN仍不能称候选。外生成本未计不等于真实0，分项归因不证明预测alpha。
- 正式仍需Root绑定本seal的release，至多一次；失败/超帽保留首失败，不允许纠后再次formal。待正式原件再独立全账守恒、终端、summary与三层状态及资源验收；当前不预判任何净额。

本次只写本review目录，旧原件/结果/STOP/其他Owner不动，未联网、新取数据、安装依赖、调用模型、连接账户或交易，也未访问保护Library目录。
