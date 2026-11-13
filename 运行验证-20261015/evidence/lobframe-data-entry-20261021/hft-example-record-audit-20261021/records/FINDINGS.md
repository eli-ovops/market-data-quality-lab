# Making Multiple Markets：固定源码与公开原件追溯

读取日2026-10-21。只读教程JSON/源码及完整Git tree元数据；没有运行Notebook/源码/模型/回测，没有获取行情、延迟或统计NPZ包，也没有读取旧A。仅写本records目录。

## 1. 版本已固定；同一Notebook确有三类延迟，当前网页同构性UNKNOWN

本次官方GitHub HEAD为 `5f3ec40b2afb764e0fea112f941ed85523ef4e88`，API返回提交author日期2025-12-23T15:31:05Z。tree `4366eba9fcaa08258c5a18e2219aabf95e64ab2d`完整282条、truncated=false。

精确对象为[examples/Making Multiple Markets.ipynb](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/examples/Making%20Multiple%20Markets.ipynb)，Git blob `0cdb26ef75895cb23bb64697d8a52d9dd70c5dbf`，1,068,659B，实际JSON SHA256 `fd01ea701d4268b0f3a8dcba4cb1cf7294e40705d326514d9f83d5f6bda2924e`；按Git blob公式核对一致。33 cells的全部source已提取为惰性文本，Notebook无执行。

以下cell编号均零基：cell3读取feed_latency，cell12读取amp_feed_latency，cell16读取live_order_latency，均配July1—31 2023行情与June30 EOD快照。后续cell22/25是简化模型，仍使用整月live_order_latency；cell30是July31单日及July30 EOD快照，也使用live_order_latency。共6次backtest定义，不能以只读初段推定同一固定Notebook仅有feed。

当前exact文档URL `https://hftbacktest.readthedocs.io/en/latest/tutorials/Making%20Multiple%20Markets.html` 的本Owner第5次公开内容读取，普通严格TLS GET报告HTTP403。已查LOCAL_BLOCKERS并停止该路径，无重试、身份/代理/TLS变更或换工具取同页。网页编译commit及与固定Notebook逐字同构性UNKNOWN；Root先前独立取得1199行可另作其页面证据，不能在本回执中冒充本Owner成功取得。

## 2. 代码引用/生成的原件路径明确，但固定树没有这些原件

以下均是Notebook相对工作目录路径，**不是已核可下载的公共URL**：

| 对象 | 引用或生成路径 | 所核公开状态 |
|---|---|---|
| 资产配置 | `assets.json`、`assets2.json` | 完整tree按basename搜索均0；具体资产身份、tick/lot取值未核 |
| 行情 | `data/{asset}_{YYYYMMDD}.npz`，20230701—20230731；末例仅20230731 | 树内全部`.npz`为0；未取得该月行情原件 |
| 初始盘口快照 | `data/{asset}_20230630_eod.npz`；末例`data/{asset}_20230730_eod.npz` | 是初始盘口snapshot引用，不是账户持仓回执；树内未列 |
| 延迟 | `latency/feed_latency_{date}.npz`、`latency/amp_feed_latency_{date}.npz`、`latency/live_order_latency_{date}.npz` | 树内无这些文件或输入latency目录；live前缀及正文称actual不认证具体实测时段/来源/字段/样本身份 |
| 持仓/损益/费用输出 | `stats/gridtrading_glft_mm_{asset}.npz`、`stats/gridtrading_glft_mm_lat1_{asset}.npz`、`stats/gridtrading_glft_mm_lat2_{asset}.npz`、`stats/gridtrading_simple_glft_mm1_{asset}.npz`、`stats/gridtrading_simple_glft_mm2_{asset}.npz`、`stats/gridtrading_simple_glft_mm3_{asset}.npz` | cell3/12/16/22/25/30中的Recorder.to_npz生成指令；完整树没有这些输出或stats输出目录 |

策略源码有position读取及限仓判断，Recorder.record(hbt)写统计状态，分析cell从NPZ的`'0'`记录读取并以`equity_wo_fee - fee`绘图。但这只证明源码接线；没有独立公开的逐时持仓、成交、费用或损益记录文件身份、数组字段/单位/完整覆盖回执。底层Recorder/stats实现本Owner未进一步读取，不能把假设的字段表冒充已验原件。

公开统计实现的元数据定位（本Owner没有读取这些实现正文）：[stats.py](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/py-hftbacktest/hftbacktest/stats/stats.py)，blob608433afb86f36864f3a8c896bd2a9b483f7191b；[metrics.py](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/py-hftbacktest/hftbacktest/stats/metrics.py)，bloba1d916f29ab8fe325e7c23abed0c60e27be5d615；utils.py blob4fb5ec1995aa89d5eca92b7883caea1ab19d390b。

搜索完整性仅限这一固定commit的完整Git tree及本Notebook的33个source cells。未搜其它分支、GitHub Releases/Actions附件、LFS实际内容、发布者私有存储或其它互联网目录；不能据此称原件全球不存在，也没有因路径未列就请求猜测URL。

## 3. 公开的是示例源码和内嵌图，不是可复核的完整交易账

该固定Notebook真正公开保存21个PNG输出：cell8的15个单资产图，cell10/14/18/24/28/32各1个组合图。仅核MIME/保存数量和text/plain占位，未解码/观看PNG；没有从图提取曲线、收益或私自重算。Python metadata为3.11.9，不包含足以认证原输出生成过程的完整运行依赖、资产清单或输入/统计文件hash。图的存在不能填补上述原始账及生成版本缺口。

cell0声明该教育示例基于0.005% maker rebate，代码调用`.trading_value_fee_model(-0.00005, 0.0007)`；这不是个人现行费率或真实到账证据。cell0还明确标注交易强度half-tick单位问题并为保留既有结果而不改例子。cell32在July31扩展案例用该段SR按`(sr-sr_m)/sr_s > -0.5`筛资产，不能将其当未经筛选的冻结整月组合。这里仅记录源码条件，不执行、解释为新策略或复算利润。

已复用2026-10-18的小样本和连续来源报告：旧实际BTC.gz仅344.803177917秒，覆盖2024-08-08末段，不能替代本教程July2023的多资产行情/延迟/账户原件。旧支持者目录有证书主机名故障，本轮没有重新访问、修复或找别名绕过。仓库15份gz示例只按当前tree见元数据，本轮均未获取。旧报告的样本许可/QC与这一教程输入及输出的完整性仍为不同证据层。

结论：当前可复核到固定示例源码和保存的图形输出；无法仅据这些证明个人可复现扣费净收益，所需的同版本资产配置、行情/延迟输入及逐时交易账仍UNKNOWN。本次没有新策略、模拟或执行许可。

## 读取账与未核范围

5项公开内容读取：①gh代码搜索（空结果，仅线索）②HEAD元数据③固定完整tree④固定Notebook blob⑤exact文档GET403；另有skill要求的gh auth status，只记认证状态核查，不输出凭证。按最保守外部操作计数共6项，没有用剩余预算扩展。HEAD的精确逐请求UTC/HTTP头未留，只有当日与CLI exit0；doc请求精确UTC/403异常已封存。未请求任何`.npz/.gz/.dat/.pkl`行情或记录payload。

只读重用的旧报告/hash见prior-evidence-reuse.json；当前具体目录搜索见tree-search-results.json；Notebook cells/MIME见notebook-cell-metadata.json；所有输入/生成路径见referenced-record-paths.json。actual model/effort UNKNOWN；新增付款/安装/下载行情/源码执行/模型/回测/交易均0。
