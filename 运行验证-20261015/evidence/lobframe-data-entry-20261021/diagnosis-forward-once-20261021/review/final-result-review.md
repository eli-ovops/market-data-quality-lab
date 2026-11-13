# 一次E/S诊断：独立有限原件验收

审阅UTC：2026-10-21T07:23:08Z。
审阅Owner：lobframe_minimal_economic_review；沿用原路由，实际model/effort为UNKNOWN。

## 验收结论

在已批准的单次训练管线诊断范围内，可接受本轮结果报告；无must_fix。该结论是静态代码加封存原件验收，不是重复前向或独立重算。

E原终态复核满足0.001bp²门槛，E先封存再运行S；固定最终A权重、同第20轮分批下，BN统计来源切换使训练MSE降低4.711072698653254bp²，但S仍未胜训练均值基准。预设分类BN_SOURCE_LOWERS_MSE_BUT_S_NOT_BELOW_TRAIN_MEAN与原件一致。原训练STOP保持，不续跑B、验证、测试或费用账。

## 实际审阅原件

相对../owner/：results.json、pass-E-seal.json、pass-S-seal.json、input-identity.json、manifest.json完整读取；events.jsonl只读pass_started/pass_sealed/diagnostic_completed事件；bn-preactivation-moments.json只定点读每层汇总样本数、批数、尾批元素数及保存计数。沿用先前完整代码静态审阅及授权检查，没有重新执行适配器。

另对manifest列示文件、E/S预测数组、排列数组、目标数组及五个受保护原件做纯文件级SHA256核对。数组/权重仅按文件字节哈希，没有作为张量或数组加载，没有读取其数值。实际哈希与manifest/seals匹配。manifest本身SHA256为ebdfe967912c630e0a789f7ef1a575620b8fa697ae47365bdf09c417cd5ff52a。

关键封存身份：

- 当前执行代码：3974f05494e06dfdce8c773ad736e80965aef4092cf815e2a5a60cde06e50261，与正式前向前所审版本一致。
- results.json：79f8c8516d4d8bfc0ef3d591c3a5208c8fe0fc41eaeffdb2e28cc9c6890a8c10。
- E预测文件：8a969a3a57730d97fadd57645e6d3ac191e95564fbbe4f5eaf42f604a35a1e79。
- S预测文件：9cdc3bbd8a1a43fbd338ff9faa36a8bd266f7f9871ce113295281160093bc44b。
- 原A权重：fa200c539704f1e78d69c47519980947c589dba1d5e5ea72a6a40cf89e5aa637。
- 原terminal STOP：6f37b1f1de6441500181531e4ac9acf570145a35cfc9cea9dfdcfcd90317bc1e。

原experiment.py、training-statistics.json、training-samples.json的当前文件级哈希亦与封存常量及前后回执一致。未修改任何Owner原件。

## 口径、顺序及状态

input-identity记22413训练样本，原X/y哈希及逐项样本身份匹配。累计20轮排列哈希20a3eaeb0cc54c6b19dec638ea018cc35701e553c1abf190664982d71e1649dd与旧fit一致；第20轮order文件已封存。两模式均351批、末批13，先前静态代码确认共享同一order。

事件顺序：E开始07:18:42.055047Z，E封存07:20:13.114382Z，S开始07:20:13.115797Z，S封存07:21:41.097926Z，diagnostic_completed为07:21:41.116078Z。未出现S先于E身份门槛通过的证据。

E/S各完整一次的seal与代码执行路径一致。两模式state_before/state_after均为56bbe0e9175956e6aaa88e148b8d9f17636c20b238468f3b3a3cb5062b850486；代码每批亦检查该摘要。BN汇总的每层batch_count均351，保存计数均7020；尾批每通道元素数为26000、13000或1300，与H100及对应W一致。未见持久参数或buffer更新证据；optimizer_steps=0、buffer_updates=0符合已审代码。

## 误差与分解的有限核对

| 已封存指标 | E | S |
|---|---:|---:|
| MSE，bp² | 77.79015510624939 | 73.07908240759613 |
| 预测均值，bp | 2.3637924470292857 | 1.641587571027226 |
| 均值偏差，bp | 2.656878231788987 | 1.9346733557869276 |
| 预测方差，bp² | 1.4897824402940154 | 0.4285011265621793 |
| 预测/目标协方差，bp² | 0.05283144789911975 | 0.21970666787867188 |
| 偏差平方，bp² | 7.059001938554174 | 3.7429609935918515 |

目标均值−0.29308578475970143bp、总体方差69.34703362319944bp²相同。原件的MSE恒等式残差E为−1.4210854715202004e−14bp²、S为0，且与先前已审总体矩公式一致；本验收没有加载预测向量独立重算这些矩。

E复核原77.7901551285931bp²在既定容差内。S仍高于精确均值基准69.34703362319944bp²，所以不能借本诊断解除原训练能力失败。S相对第20轮在线损失换算值仍差3.8608187824079465bp²；因此BN来源的受控效应并未解释全部在线/终态差距。

均值偏差、预测方差与协方差共同参与此次差异；这些是同一预测向量的描述性分解，不证明均值校正、BN校准或任何新配置可修复模型。本轮也没有隔离哪一BN层、哪个通道、无偏修正因子、最后小批或最后Adam步为根因。

## 资源及解释边界

末次completed预算回执记含静态预检与导入的计算墙钟192.8492766660056秒，进程峰值RSS1037254656字节，新单元已计磁盘984793字节，线程设置6，完成时间早于09:10:22Z截止；与资源帽有明显余量。这是执行进程回执，不是审阅者独立资源测量；末次预算后的manifest/退出尾段以及后续纯文字交付不冒充已被该数值精确覆盖。旧数据下载阶段真实峰值UNKNOWN，本诊断没有新增下载。

结论仅为：在固定最终权重和该训练批划分下，改变BN统计来源确实改变误差，并带来上述改善，但仍未过训练均值门槛。S使用同批其他样本统计，可含相对单个样本的未来市场信息，不能称因果可部署、样本外能力、校准成功、策略修复或盈利证明。原FAILED/STOP和留出未评估状态保持。

本审阅无CSV/测试读取、权重或预测张量加载、模型运行、额外前向、反向、重新拟合、费用回测或交易；仅阅读回执/摘要文本、文件级哈希并新增本记录。后续Owner文字说明若另存附录，不应改写已封存结果及manifest；本记录不声称已经审阅尚未提供的附录。

## 同轮补充交付核对

补充审阅UTC：2026-10-21T07:24:47Z。Owner随后提供FINDINGS.md、postrun-receipt.json、completion-manifest.json，本审阅完整只读这三份新交付；另对它们及moment-comparison.json做文件级哈希。未详细审阅moment-comparison.json的层级数值，不据其提出通道根因或新模型结论。

FINDINGS.md与已封存结果一致，明确原STOP保持、S不可部署、没有样本外或盈利结论。postrun回执记录唯一正式PID25785/session60787、exit0；追加标准库汇总无额外前向，helper墙钟0.004871041979640722秒。此为Owner执行回执，本审阅没有独立运行该汇总或测量其CPU用量。completion-manifest的旧运行manifest、结果及预测哈希均延续不变，新增说明采用独立附录，没有改写已验收运行原件。

新增交付实际SHA256：FINDINGS.md为7311d894a1fa57573e87b63d635e49a56709d93035400183233a8585332ec791；postrun-receipt.json为d7881a57cec6cb6204bd5d5c46a522f6a4d022d5037d295d5ea0211278a0c810；completion-manifest.json为3d656d1734ba506538a322aa9125bce5a6269aa07002a329560d1904daca496a；moment-comparison.json为c48767b5060273b392811e606f0b6c8a4221eed03cfa6dc431ec6f8acfcf815e。无新增must_fix，有限验收结论保持。
