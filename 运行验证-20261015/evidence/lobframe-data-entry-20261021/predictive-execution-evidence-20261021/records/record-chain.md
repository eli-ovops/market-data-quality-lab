# 预测—执行—费用：现有原件链核查

结论：这三个已收口单元中，**尚未取得一组可逐笔绑定“预测前可知输入→当时预测/决策→实际订单→实际成交→实际扣费结果”的原件**。这是当前取得材料的边界，不是认定作者从未记录、策略不可能赚钱或研究必须公开私人账户。本轮不联网、不重审模型、不提出调参/运行，不改旧STOP。

本轮只读三个最终报告、各原件可得性/引用清单及两份最终独审报告，没有打开行情、权重、预测、订单或收益数组，也未重新读取来源代码/PDF。下述作者事实与数字均沿用这些已核报告，不冒称本轮独立核原始交易账。

## 1. Albers：已有最接近赚钱判断的作者正面报告，缺口是原始链未公开/未取得，而非“作者未做订单记录”

[最终报告](../../reversal-model-evidence-20261021/短期预测正面证据-机制与复制门槛-20261021.md)及[原件清单](../../reversal-model-evidence-20261021/artifacts/artifact-availability-review.md)记录：作者实际采集最小maker订单及其成交/撤单结果，研究模型使用投稿时可见输入，报告后半周约3.5日结果。**存在真实订单实验的论文陈述，不能写成纯行情分类、完全没有记录成交。** 但Data Availability明确数据不公开；本地未取得逐单输入/预测时间、订单标识、成交、撤单、退出与费用记录。模型筛选策略的表格结果也不能自动认证为一份按该规则实时下单的账户账。

已经直接改变赚钱判断的公开证据是Table4的费用拆分：作者重点阈值.24往返均值+.71bp，含固定1bp返佣，价差项−.29bp；相邻.26行+1.21bp、价差项+.21bp。它说明“同费用假设下筛选改善”与“普通个人付正费用后还赚钱”不能等同，也不能说所有价差项均负或利润全来自返佣。这些是已发表均值的有限正证据，不是我们核得的实际收费到账；最有利费率和忽略时延的假设仍在。

能改变闭环判断的原件应将既定规则及预测时点与同一批实际订单/成交/退出绑定，并区分实际收付费用与假设返佣；目前只取得论文与参数/表格文本，不能由报价或表格补造该链。缺口分类：**报告明确说采集过订单，研究数据明确不公开；实际费账与实时规则执行绑定未取得/UNKNOWN**。

## 2. Globe：取得的是预测论文与源码，尚未取得实际交易或扣费结果；不能把准确率当缺失环节的替代物

[最终报告](../../globe-two-second-admission-20261021/两秒预测-准确率与赚钱证据-20261021.md)及[原件清单](../../globe-two-second-admission-20261021/artifacts/availability-and-license.md)取得固定作者代码、分类表及下载链接引用；没有取得可绑定论文结果的数据归档/权重，更没有实际订单、成交、费用及退出账。精确Dropbox链接和GCS/本地路径只是引用，不是原件取得或交易执行回执。

已经直接降低“headline证明赚钱”可信度的证据是同表多数类基准75.31%高于主结果约71%，以及71%/76%分母未绑定；方向recall仍有信息，不能因此一笔抹去。无论采用71%还是76%，平滑mid分类仍没有提供“以什么价格成交、最终付多少费用”的经济量，因此这些指标本身不能给净利下界。

缺口分类：**现有报告/原件范围没有实际订单与扣费结果这一证据层**；这不同于“已报告实际盈利但私藏原账”，也不能扩大成“作者现实中根本没记录或没交易”。会改变赚钱判断的必须是预测在先且能与实际执行及成本绑定的独立结果；再增加分类数字不会补上链条。

## 3. HftBacktest：记录器和扣费接线公开，原统计包未取得；模拟结果不因live时延文件名变成实际成交

[最终报告](../../hft-example-record-audit-20261021/案例结论-执行方法可复用但非盈利预测原件-20261021.md)、[原件报告](../../hft-example-record-audit-20261021/records/FINDINGS.md)与[引用清单](../../hft-example-record-audit-20261021/records/referenced-record-paths.json)显示固定Notebook有下单/持仓及Recorder接线，生成六类stats路径，分析权益时实际扣fee；不是“代码根本没记费用”。Notebook保存21个PNG，但固定tree未列对应NPZ、assets清单、July2023行情及延迟包；本地未取得这些原件。代码会生成与文件已公开、结果已取得是三种事实。

现有记录明确这些订单/持仓结果来自历史回放模拟；live_order_latency即使源自实测，也只是回放参数，不能证明教程输出对应真实订单。旧数分钟2024 BTC行情样本不能填补2023年7月多资产执行账。该例也未提供本轮目标中的可复用价格方向预测器，故不能把模拟做市曲线接成已证实的预测优势。

已能改变赚钱外推的证据：代码扣入最高档maker返佣，个人资格未证；末个July31扩展示例用同段Sharpe筛资产，不能当事前固定独立组合。缺少完整成交额/费账时，不能确定去返佣后收益符号，也不能称全部利润由返佣构成。缺口分类：**公开代码明确设计了模拟记录与费用计算，图形结果已保存，但对应原统计文件未取得；实际账户订单/手续费链并非这份教程已证明的对象**。

## 阅读范围与可追溯身份

仅上述最终报告及其指定原件清单、既有独审；没有扩扫其他项目、原始行情或已关闭模型，也未新增网络、下载、账户或交易。不存在通过这次检查补出的原始交易证据。已取得的论文/源码/hash可以绑定文档身份，不能单独绑定某次历史真实交易执行。

以下SHA256只针对本轮所读报告/清单文本，未重验数据或数组：

- `reversal-model-evidence-20261021/短期预测正面证据-机制与复制门槛-20261021.md`：`35e7d1f9ce6ae2ef1ea36051c9074f00cafe4d16c05fdf850c98ed530f2d56ac`
- `reversal-model-evidence-20261021/artifacts/artifact-availability-review.md`：`63e91e744b955dc9c8a314d136e80d70cf5884b2b87da082f74a431bfb9d728e`
- `reversal-model-evidence-20261021/artifacts/artifact-source-receipt.json`：`862f09331b9fb4e0eca1497dedfbc92e4ad0bb5e68fe900719dac0e8c9d058e6`
- `reversal-model-evidence-20261021/root/final-independent-review.md`：`1ba89f1a3da54ebf1a585ec44335fdfba1e61746a43920732555db60b91fdde0`
- `globe-two-second-admission-20261021/两秒预测-准确率与赚钱证据-20261021.md`：`6ba2667e72101a95af56712788bc235f0f475586e6196dd9aa5fa3a201af8fef`
- `globe-two-second-admission-20261021/artifacts/availability-and-license.md`：`6eb505b83d3643ffb06d2fdf410fd1054de369c4595eda0a14b8b91ac2da8f02`
- `globe-two-second-admission-20261021/artifacts/availability-receipt.json`：`fde3d784739593c264172566d6679c1c38238b99a760b567b5b88c2be9e3cb48`
- `globe-two-second-admission-20261021/root/final-independent-review.md`：`26e99a2fac359a84decbe6bd7dd7242d0ad335695e56c6474f7e0e13cbc74f15`
- `hft-example-record-audit-20261021/案例结论-执行方法可复用但非盈利预测原件-20261021.md`：`7998239acb0f389603a3ca62a15c689859e6ece0545004a69d0b44f4868499a0`
- `hft-example-record-audit-20261021/records/FINDINGS.md`：`482c44d52290e36358d2a6d842f9c93ef31700ddf26f52b9b357a2fbeefaf789`
- `hft-example-record-audit-20261021/records/referenced-record-paths.json`：`6d2dfd4eb702790a198f4939dc6b872a1fcd98bdc9baa008a391308149ea4ea5`

完成UTC：2026-10-21T08:41:57.610600+00:00。规则PERMISSIONS-2026-10-14-v1 / ROUTING-2026-10-13-v4沿用；实际model/effort UNKNOWN。唯一新增文件为本record-chain.md，无模型计算/付费/安装/下载。
