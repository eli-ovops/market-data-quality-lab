# 纠错单元独立终验

审阅UTC：2026-10-22 11:19:27。**ACCEPTED_WITH_LIMITS；must_fix=[]。停止推进当前固定报价/费用组合**：纠错后现金必要条件已经可判，8格F净额全部负。结论不依赖把风险UNKNOWN算成已知失败，也不再依赖旧有缺失订单的条件子路径账。actual model/effort/speed UNKNOWN。

## 实际验收覆盖

已读唯一formal的started/completion、退出回执、resource-formal、terminal-seal、Owner报告全文；实际审两日summary的全部16条路径（完整现金状态、空execution未知列表、risk未知计数/首例、成交/决策分母和归因状态）、result的全部8比较及双方风险值。Owner报告与原件均是两日各00:00:05–09:00:49共同约9小时前缀，不是整24小时；每条路径32,445决策格。

复用并事前适配独立`review/audit_saved_ledger.py`，**只运行一次**，未import原策略代码或重建信号/队列/风险路径。实际工具session61307，PID50623，exit0。逐行覆盖May 1,225,415、June 1,109,271，共**2,334,686行**；全部fill分别1,411/3,038，共**4,449笔模型成交**，以及16条终端完成记录。流式读至gzip EOF，现金/BTC/费用逐行恒等式、费率、非fill余额不变、终端BTC及预留归零、各路径fill数和最终余额对summary全部匹配。

机器回执为`saved-ledger-audit.json`，包含账本header、全部fill的摘要hash、逐路径计数、首/末fill及全部终端小见证；本Reviewer实际读取终端见证及全部摘要字段。程序检查全部行，人工未逐字阅读230万行，不冒称第二份撮合真实性验收。`audit-tool-exit-receipt.json`保存实际工具退出/PID/CPU/RSS与8格双方原风险值；`terminal-file-identity.json`对17份必要原件实际bytes/hash匹配final-manifest，并对terminal-seal内引用、正式release及源码seal闭合。

账式验收实测CPU10.951893秒、wall11.876431秒（从脚本标准库导入后计时），峰RSS12,697,600字节；35CPU秒硬保护及128MiB核验限度未触发。文件身份辅助CPU .023466秒。它们计入新review/root60秒共享预留，不是另开资源帽；静态期未单独仪表化的极小hash用量精确值UNKNOWN，不伪造完整OS计量。没有重跑Owner合成或formal。

## 现金与分层结论

16条路径execution_cash_status均`COMPLETE_CONDITIONAL_MODEL_CASH`，unknown均空；终端现金/BTC/费用实际闭合。result及两日summary逐路径相同，Δ只在双方完整时计算；独立核对8格Δ为已有F净额减H净额，各状态均`CASH_NECESSARY_CONDITION_NOT_PASSED`。整体`FIXED_COMBINATION_CASH_NECESSARY_CONDITIONS_NOT_PASSED`与其一致，`has_execution_cash_unknown=false`、`has_risk_unknown=true`均正确。

|日期|情景|F净额USD|H净额USD|F−H USD|
|---|---|---:|---:|---:|
|May1|E100|−3.0678|−2.8618|−0.2061|
|May1|E500|−4.6006|−3.9453|−0.6553|
|May1|X100|−33.8095|−34.8474|+1.0379|
|May1|X500|−42.2043|−43.3238|+1.1195|
|June1|E100|−6.4736|−5.2990|−1.1746|
|June1|E500|−5.3644|−4.1094|−1.2550|
|June1|X100|−97.4048|−88.6693|−8.7355|
|June1|X500|−114.9546|−118.2122|+3.2576|

表复述已保存报告的约4位展示，精确值在result/summary及上述机器回执。三格正Δ是比H少亏，不能说赚得正利润。8格F自身均负，已足以不满足固定组合原必要条件，无须放宽风险阈值求判或另加费率情景。

**整体风险可比性仍UNKNOWN，不是每个风险量都无法计算。** 库存BTC秒为已保存库存×时间积分，不依赖价格参考；执行现金完整后可作为独立数量时间暴露列示，本次只核汇总传递一致，未重新积分。最大库存美元名义与最大净变现回撤依赖合格价格参考，持BTC期间缺参考使其当前数值只代表已观测可估值时点的最大值，不能认证完整最大值/风险上界。8格双方三项原值均保留在audit-tool-exit-receipt的comparisons，且risk_complete_both=false、F≤H比较null，没有用局部小值冒充风控通过。风险一秒阈值未变。

归因16路径仍UNKNOWN，不从现金负数推断亏损只来自费用/库存漂移，也不把参考价漂移称报价收入。完整现金是**有限条件模型**的完整性，不等于本人真实可得成交、实际个人费率/总外生成本或完整个人净利。

## 版本、唯一执行与资源

实际必要原件身份均匹配：preparation-seal `fcc3295c53afb72181d4ce46bbed69c811bf5efe0a4af41b278eaa5130a88cbe`；result `fd9c510127231b967b9c934d963ccedd20efdf6f941a267b1c5bd9b17c5117d2`；final-manifest `826686320f6c044a5d2996d7703465d596bc1ff241315b4d7e01f1d9e577aa69`；terminal-seal `9a590945dec619e0069e22a703a46cbaba5ed30f30afe570c16924ae6e5b46c6`。正式源hash等于已审seal，release绑定相同seal，未见事后改源码或重跑。

唯一正式session35939、PID49526，项目.venv Python3.12.14，UTC11:15:02.596667启动至11:15:57.957686完成，exit0、stderr空、formal marker保留。此与工具退出回执及正式start/completion一致，不把本次文件审阅声称为独立穷举OS历史进程。原单元、旧UNKNOWN和所有STOP不变。

formal记录CPU54.659405秒、wall55.374739秒、峰RSS172,933,120字节、单线程，记录时Owner输出25,506,358字节；含prepare新Owner脚本累计54.761166秒，另文件封存小CPU .048073及文档封存 .045935。旧150秒和新review/root60秒是保守借记，不是旧实测或资源清零；脚本记录264.761166秒含借记，另收尾/独审在既定余量内。所有已见原件在新Owner390/共享600秒、512MiB、64MiB、UTC13:08:23.097535截止内；RSS/目录值是记录范围，不冒称瞬时OS隔离或全平台精确CPU计量。

## 继续/停止的适用范围

此次已完成有信息量的纠错：原984条改善报价排除可在同缓存解决，已不再用它们导致的UNKNOWN避开现金判断。结果支持停止**这套固定信号、报价/库存政策、四情景与费用组合**继续晋级，不支持投入真实资金，也不通过改风险、费率、日期或多轮重跑挽救本次结果。它没有否定全部成交流信息、所有做市模型、其他原理或XTX生产能力。

两日早已被用于研究，仍是同样本内模型诊断，不是独立样本外/前瞻证据。结论已经可由原现金必要条件收口，本轮无须为风险UNKNOWN再开研究才能停止此配置；也不自动授权任何新策略或实验。只写本review目录，无新行情、网络、依赖、模型训练、账户钱包或交易，保护Library未访问。
