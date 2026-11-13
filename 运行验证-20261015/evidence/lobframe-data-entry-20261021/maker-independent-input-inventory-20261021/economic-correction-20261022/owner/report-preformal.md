# 离线纠错验证准备回执

状态：READY_FOR_STATIC_REVIEW_NOT_FORMAL。本新单元尚无formal-started/first-stop，未运行真实数据经济回放。

已完整读root/brief.md、authorization.json，按用户对原两日F/H四情景纠错单元授权推进。只在本单元owner写入；旧economic-execution-20261022、源数据/原方案/STOP/他人文件保持。

实现从旧core/inputs/run/tests/spec独立复制后作有限修改：

1. core接受处先保持原post-only检查，再对strict bid<ownL<ask的改善价设可见ahead=0；仍属无隐藏量/无先插队模型假设，不证明实际队位。原同侧best、内部空价、真正深档UNKNOWN、陈旧/冲突参考处理不变。
2. path结果单列execution_cash_status/risk_status/attribution_status。完整F净额<=0独立失败，即使H或risk未知；F−H只在双方现金完整时解释。F现金正且增量正仍必须原三风险指标完整且F<=H，风险UNKNOWN不能晋级。归因不是新增主门槛，条件子路径负数不能冒充完整亏损。
3. 必要隔离runner/资源适配：新目录、授权/Root release绑定、UTC13:08:23较授权小数截止略严格；新Owner390CPU秒，旧150秒保守借记及新审阅60秒，不冒充旧实测。1线程、512MiB RSS、64MiB新输出、网络/新数据/下载/安装/付款0。

47纯人工合成PASS，prepare exit0，实际.venv/bin/python3.12.14；新增双侧改善、同侧best、内部空价、深档未知、对手best拒绝、参考缺失不救单、部分fill/穿价/取消守恒及现金完整风险未知等分层边界。原parser深层冲突/精度合成保留，inputs.py与旧reader逐字相同（对应diff为空）。没有用新真实结果校准任何规则。

prepare资源原件：CPU0.063858秒、wall0.043825秒、峰RSS30064640字节，单线程，记录时新输出103785字节。文件封存小额CPU另记资源，不清零；旧150+新review60只是保守借记，实际记录分开。新正式最多一次，首失败/超帽永久停止，不修后重跑。

完整旧→新差异：complete-source.diff及五份逐文件diff；真实源码/测试/spec与输入metadata/小raw身份均由preparation-seal.json绑定。原47合成结果和source_hashes在synthetic-receipt.json，stdout/stderr/资源回执均保留。

当前preparation-seal SHA256 fcc3295c53afb72181d4ce46bbed69c811bf5efe0a4af41b278eaa5130a88cbe。Root正式release合同沿既有status=RELEASED_ONE_FORMAL_ECONOMIC_UNIT并绑定本新seal；独审与Root放行之前不formal。

actual model/effort/speed UNKNOWN，目标沿原gpt-6.1-sol/medium，仅凭followup不能核实实际设置。规则PERMISSIONS-2026-10-14-v1、ROUTING-2026-10-13-v4、HANDOFF-2026-10-10-v2。保护Library未访问。不新建Owner或子agent，不连接账户钱包或交易。
