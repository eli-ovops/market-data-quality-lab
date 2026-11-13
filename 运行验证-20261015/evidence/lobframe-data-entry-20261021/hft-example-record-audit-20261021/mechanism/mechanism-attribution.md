# Making Multiple Markets：机制适用性只读审阅

读取日：2026-10-21；收口 UTC：2026-10-21 08:07。实际 model / effort：UNKNOWN。角色为原独立审阅 Owner；原训练 STOP 及已结束诊断均不改变。本轮仅阅读公开正文、代码文本与 records Owner 的 inert source，不运行 Notebook / 代码，不读取行情、权重、成交或收益数组，不做重新核算。

## 三项决策发现

1. **此示例未提供用户要找的可复用价格方向预测 alpha。** 两版报价函数的中心都是当下 mid 减库存偏移；回归拟合的是交易到达强度随价差的衰减，价格变化用于估计波动。它支持报价宽度、成交强度校准和库存控制的机制研究，不能充当 XTX 预测模型的复刻证据。定位：官方页 L147–180、L730–760；本地 inert source L150–183、L700–731。GLFT 原论文的基础参考价格无漂移；§5.1 另行加入给定漂移 μ，并没有替使用者提供一个经验证的方向预测器（PDF 第4页 §2、第12页 §5.1）。不能因此宣称 GLFT 排斥方向信息，也不能把外生 μ 当已取得 alpha。

2. **live_order_latency 是历史回放的时延输入，不能据文件名认定有实盘正收益原账。** 同一页面依次有 feed、amplified feed、live order latency 的 backtest 重定义，后半简化版本也使用 live 输入；应分别识别，不能只读首段或混拼其他教程。live 数组传给 `intp_order_latency`，随后建立回测对象和记录器；这里生成的 stats 属模拟输出。定位：官方页 L244–283、L418–457、L535–574、L829–867、L948–985；inert source L510–530、L809–835、L913–940。未读时延文件内容，因此其实际采集方法、账户来源、与实盘成交账的对应关系均 UNKNOWN。即使时延来自真实测量，也不使后续模拟成交和资金结果变成真实成交及资金结果。

3. **它不解除当前个人经济可行性的证据缺口，也不应替换原研究方向。** 页首自称“educational purposes only”，假设 maker 返佣；代码同时固定排队、无部分成交和费率模型，且页首披露到达深度的半 tick 单位问题未改。定位：官方页 L17–18、L553–556；inert source L17–24、L518–521。于是其结果不能直接证明用户可取得同费率、成交质量或容量，更不能证明 XTX 私有盈利机制。反过来，也不能仅凭返佣存在就断定全部模拟利润只来自返佣。records Owner 另核 cell32 对 July31 扩展组合按同期 SR 筛选，故该组合也不能称未筛选样本外组合；此为分工证据，未独立读取收益数组。该例只增加公开报价控制的参考证据，未证明用户已有可复制且全成本后盈利的预测环节；不据此启动网格、做市或新模型实验。

## 仅固定成交记录的费用恒等式

令 V_m、V_t 是同一组固定成交按相同计价单位计算的 maker / taker 成交名义额；费用率取带符号值，负值为返佣。若价格、数量、成交身份、库存估值和其他成本全部固定，且费用按成交额线性计提，则：

`P_new − P_old = −(f_m,new − f_m,old) V_m − (f_t,new − f_t,old) V_t`。

P_old 若已经扣除旧费用，只加上述差额，不能再扣整笔新费用；价差、滑点等若已体现在成交价，也不能重复扣减。本轮未读取 V_m、V_t，未计算任何收益。此恒等式不识别费率改变后报价、下单、排队、撤单、成交身份或成交量的变化，也不构成新费率下策略的反事实收益。其他《Impact of Order Latency》案例、April 表格及初始化差异不并入本案。

## 来源与冻结身份

- [官方教程 exact URL](https://hftbacktest.readthedocs.io/en/latest/tutorials/Making%20Multiple%20Markets.html)：本轮读取1199行，含后续重定义；`latest` 发布时间 / 文档构建 commit：UNKNOWN。本地 records Owner 提取的 source 与所核函数和分支一致，不读取其输出值。
- [GLFT 官方论文固定 v5 PDF](https://arxiv.org/pdf/1105.3115v5)：arXiv v5 日期2012-08-03；作者 Olivier Guéant、Charles-Albert Lehalle、Joaquin Fernandez-Tapia。基础模型与漂移扩展定位如上。
- [教程简化段实际链接的 Optimal market making](https://arxiv.org/abs/1605.01862)：作者 Olivier Guéant；页面 v5 修订2017-05-06。本轮仅读摘要，未把它与2012论文或其公式版本混称。
- 本地只读文本：`../records/notebook-all-cell-sources.inert.txt`；身份元数据：`../records/notebook-cell-metadata.json`。元数据记 notebook SHA256 `fd01ea701d4268b0f3a8dcba4cb1cf7294e40705d326514d9f83d5f6bda2924e`、Git blob `0cdb26ef75895cb23bb64697d8a52d9dd70c5dbf`。records Owner 经 Root 回传的 commit 为 `5f3ec40b2afb764e0fea112f941ed85523ef4e88`（2025-12-23），本轮不重复 Git 查询。tree SHA `4366eba9fcaa08258c5a18e2219aabf95e64ab2d` 单独保留，不能误称 commit；HTML 与该 commit 的构建绑定 UNKNOWN。

官方公开页面合计3个；未新增外部作者联系、下载数据、执行或实验建议。以上是源码 / 正文的机制归因，不是实盘账验真，也不是独立复算教程结果。
