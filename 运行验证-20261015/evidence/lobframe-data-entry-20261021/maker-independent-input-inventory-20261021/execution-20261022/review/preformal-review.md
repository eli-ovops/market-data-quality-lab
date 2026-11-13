# 两日挑战：正式前独立静态审阅

2026-10-22；精确UTC起止UNKNOWN；实际model/effort UNKNOWN。当前正式未启动。未执行来源代码、合成checks、行情获取、标签/费用计算或模型。

**实质方法逻辑PASS_WITH_LIMITS；当前封存/解释器项待闭合，故尚非正式ready验收。** 不重开已审方案，不增加新指标或执行许可层。

## 通过的实质逻辑

- `analysis.py:36—49`：只取名义最新as-of参考，接收区间上界须小于目标下界，下一名义报价若跨目标亦UNKNOWN；不跳回旧行救覆盖。年龄按最坏边界≤1s；BBO与trade源钟各±10ticks后严格比较。L8—33按同接收戳组检查四个BBO价量，冲突/源钟回退标坏。
- `analysis.py:74—114`：分笔计数只用[t−1,t)；capture边界含糊则网格UNKNOWN，hash仅同一非零z网格。历史source最大值来自截至t之前的全部trade，不限过去一秒、不借未来；未来报告的源钟严格大于该最大值。只有collector/字段时序意义，不证明本人可撤单。
- L117—124、143—193：先由时间/source guard/合格参考挑每日首个被动ID，再接z/hash；零分、无评分、输入未知不让后续成交替代。首次同capture整ID UNKNOWN。固定全trade分母在参考/评分未知过滤之前计数，80%是原固定分母之比，不填零。
- L134—140、194—226：网格内订单等权、每policy×方向的有效网格等权，再方向/两日等权。bootstrap每天48个UTC30分钟块、四cell共同抽样，用sum/count重算原统计量，不平均块D；1999次、固定seed、缺cell复样不补零且须≥1900有效复样。现有43项合成回执包括手算权重和bootstrap例，不冒充真实效果验证。
- L52—60、150—160及run.py原L29—40：双侧辅助费用按冻结式一次入账，滑点只作用于退出报价，不重复扣spread；0费仍有退出滑点。辅助结果不gate方向统计，不生成个人现金账。D/区间通过仅为带暴露历史条件候选，不是同活动风险因果净利、获单或容量证明。
- `core.py:135—223`：固定串行288片、无认证/重试/redirect，压缩或identity按实际头解释；分片身份/时间/type/ID/正有限值及gzip结束校验；明确空行才构造断连区间，静默不当断流，重复ID/片界/异常停。正式入口保护first-started/first-stop，实际缓存hash及封存身份再绑定。未见实现将旧实验STOP解除。

## 资源与证据

Budget继承全部resource记录（含Root保守预留），网络和compute分账、主动截止固定UTC01:59:57；下载字节剩余额限制读取，周期SIGALRM检查时间/RSS/磁盘，无每阶段清零。RSS/磁盘是运行期周期检查，非OS瞬时内存隔离；不得在最终报告冒称瞬时峰值被硬隔离或所有跨角色资源均独立精测。已读准备预算194.789711秒计算扣减，含190秒保守预留；网络60秒、1MiB预留与Owner实际行情GET0分开。

完整静态覆盖四个当前源码（analysis首次显示截断后补读L60—175）、parameters、preflight、preparation-seal、preflight-reuse-amendment、preparation-budget、resource-reservations、最新43项合成回执及tests定义、Owner报告；补读当前合成/预检资源回执。旧analysis与当前diff仅将原聚合块提取为同逻辑helper，输入预检复用理由成立。未读任何真实行情或合成fixture正文。

## 待闭合（同一封存/运行身份问题）

1. 原seal的`runtime_Python=3.9.6`与preflight实际3.12.14不同；`dataclass(slots=True)`等当前实现不能将3.9写seal进程冒充正式runtime。Root已请求Owner明确合成/预检/正式绝对解释器及字段语义，无需重跑真实QC。
2. 本审最终shasum核core/analysis/tests/parameters与原seal一致，但`run.py`当前SHA为`430b521c3e1e6a9dde249cc2805ee61682701b37a54a2be5c6df61ff16091b91`，不再等于原seal的`842ffda2…`；原seal仍`1ff44d5377b4d15a83d54ab7c5ac0436497b32362e29981e47d4778cfc7f7a28`。可能为Owner正在完成runtime修复，不能当已闭合。需对应修订说明/diff和新seal，Reviewer仅核该项整改，不重审完整方法、不重跑checks。

以上两点属同一个正式运行身份封存闭合事项，不是新的研究门槛。待Owner冻结修正回执后可在既有整单授权内继续，由Root统筹内部放行；当前不按旧seal启动正式。仅新增本review，未改Owner、Root或任何STOP。

## Runtime同轮闭合：最终正式前结论

2026-10-22仅补读`runtime-binding.diff`、`runtime-binding-check.json`、新`preparation-seal.json`及run.py对应guard。新seal明确合成/预检及必须使用的正式解释器为`/Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/.venv/bin/python`，真实版本3.12.14；旧3.9.6写封存进程不再冒充实际runtime。四项纯元数据检查PASS记录拒绝错误路径/旧版本，未重读真实输入、GET或标签。`validate_runtime`在正式获取前精确比对`sys.executable`及`sys.version`，不匹配即进入已有失败停机路径。

独立小文本shasum核新seal为`f2a724017607c944f32da7cbf0ddbef0503d65fa9ae5300704fd6550cbe34a99`，run.py为`430b521c3e1e6a9dde249cc2805ee61682701b37a54a2be5c6df61ff16091b91`，与新seal一致。其余方法/解析/参数及已审43项保持原封存身份，未重复真实QC或checks。

**最终accept=true，PASS_WITH_LIMITS，must_fix=[]。** 当前方法/代码及运行身份静态审阅闭合，可以在既有完整单元授权和原累计资源/截止内，由Root按新seal内部正式放行一次；不是用户再批准请求。Reviewer不启动或复跑正式分析。保留本文件初审待闭合记录为历史，现已全部关闭；不扩大效果/利润解释，不解除其他旧STOP。
