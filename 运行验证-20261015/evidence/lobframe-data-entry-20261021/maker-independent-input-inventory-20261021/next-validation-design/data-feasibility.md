# 现有两日数据：自己的挂单与撤单能验证到哪层

**结论：可以事前定义假想订单及延迟情景；不能据现有两日数据确认自己的获单、部分成交或真实排队。** 最关键缺口是May/Jun没有已取得、可接合的逐单队列生命周期与初始状态；成交后的buy/sell_order_id不能把某笔实际成交变成自己可得的成交。当前只读工作不复用已耗用的一次执行许可。

## 已有字段与确实取得的日期

| 输入 | 已确认可用 | 不能替代什么 |
|---|---|---|
| 2026-05-01、06-01原生live_trades_btcusd，288片保存在owner/data/{date}/{offset:04d}.bin | collector接收前缀7位小数、源microtimestamp、trade ID、type、price/price_str、amount/amount_str、buy_order_id/sell_order_id；type0主动买/被动卖，type1反向，作为供应商定义的解释 | 成交以前的对方订单状态、自己的订单回执/生效时刻、完整队列、撤单先于成交是否生效 |
| 两日既有book_snapshot_25 | 每侧25档聚合price/amount，exchange/symbol、source/local时间；最优价量可作as-of参考 | 每档内部订单ID、排列、每笔新增/撤减来源；两次快照间路径、快照瞬间原子性及完整feed |
| 当前normalized Trade与gzip JSONL | cap/src/id/buy/sell/type/price及原片offset/line | **没有保留amount**：core.py:202对数量只验证，203写出的normalized记录不含数量。原始片仍保留数量。若日后另获量约束计算许可，应读已存raw原件，不能把normalized冒充完整价量逐笔；当前不读/不计算。 |
| 2026-07-01 00:00首分钟原生样本 | 真实取得6021 created、49 changed、6034 deleted，共12104订单事件；字段含ID、order_type、price/amount、amount_traded/amount_at_create、源钟/接收钟、event_id/pre_event_id；另有50 trade报告、1 generated snapshot | 不是May/Jun整日事件；不能跨日期补成其队列或拿7月局部完备性背书两日 |

此前July快照第三列与订单ID有具体等值关联，但快照source早于捕获顺序中紧邻前事件，且自身无event链锚点。按接收行收到快照便直接从下一行更新，不能凭现证当作无缝原子初始化。43/50较强事前身份见证只说明该分钟两钟先后；未重建存续状态，更不是获单或预测准确率。

## 可确认：无未来身份的事前规格能够写清

在决策collector截止t，仅使用严格已收到且时钟/陈旧度合格的BBO和过去成交流，预先写明：自己的虚拟订单标识、买卖侧、报价函数、固定量、库存约束、post/cancel规则、订单有效期和重报规则。报价可取截止前可见价格的函数，不能从下一笔真实成交价倒选；自己的虚拟ID不得借用未来buy_order_id/sell_order_id。最小价位、最小量和历史有效期规则若未另核，应标参数假设，不称实际订单合法性已确认。

可以在方案层固定观察/决策/报单/撤单时延，机械区分“发出撤单”与“假定撤单生效”；生效前仍承受可能成交。该情景是可审阅的规则，不是测到的网络延迟。本轮没有编写/执行实现，既有代码也没有自己的订单生命周期模拟。现有source/local钟及其差，不证明用户接收/计算/路由/撮合/撤单确认时刻。

## 能保守界定：报告条件风险或条件情景，不能包装成真实获单

- 现成两日结论只比较已收到真实成交的事后不利变动。可保留“若某方向当时已有挂单，其后遇到不利流的条件风险”这一研究解释；不能把未来发生的成交作为事前决定是否/在哪个价格挂单的依据。
- 对假想量q，不加额外市场机制假设时，实际成交量安全界只能是0至q，信息有限。若进一步固定非冲击历史重放、假定优先规则与订单生效延迟，可用已记录同价/穿价主动成交量约束一个**条件情景**；它不是被证明的个人成交上限/下限，因为加入自己的订单可能改变成交与后续队列。
- 聚合盘口减量不能一律视为前方队列消耗；它可能是成交、撤单、重报、补量或中间路径被采样合并。不能把所有撤减放到自己前面来取得乐观成交。对“全部在前/全部在后”等队列位置分支可以预先限定情景，但须明确它们依赖完整更新、撮合规则和非冲击假设，而现有snapshot25并不能认证这些条件。
- 不在快照25档内的报价缺深度参考；发生断连、时间边界不明、报价陈旧/冲突时，应停止该段可行动性判断或标未知，不能因标签覆盖>99%而补成完全队列。两日5个明确断连、37个受影响输入网格及46个未知未来报价标签继续保留。

## 必须未知：哪些输出不能现在报告

真实价/时间优先、同价排队、改单增减量/改价丢失优先级，在此前官方检索范围未取得明确规则；不能拿行业FIFO作已证事实。即便假定FIFO，snapshot25也不给每个排队订单及其新增/撤销时刻，故队前量、隐含优先属性、部分成交分配、撤单race赢家均不能恢复。打印交易携带实际订单ID只揭示发生过的匹配，不给自己的反事实队位。

因此：自己的首次获单时间、部分成交量、有效撤单率、重新排队损失、漏掉好成交数量及全成本净改善，目前均未确认。不能复制一笔实际被动订单的成交记录，再用事前信号“删除坏单”就称完成自己的策略重放。条件延迟网格不是个人实测延迟；是否准入/个人费率亦不由历史输入认证。

## 唯一下一数据门槛与停止条件

**优先只定义一个固定报价/固定量/固定延迟的可行动性规格，保持数据工作只读；无需现在新增数据。** 它能避免未来身份/价位泄漏，但最多形成情景研究，不能验收“自己可获单/撤单产生净增量”。

若下一轮明确授权的目标必须是队列层获单而非条件风险，最小新增来源核验应是**同一已定历史日一个事前固定短窗**的逐单live_orders：带可接合初态/锚点、创建/改量/删除及序列连续证据，并与现有trade双钟配对；同时需要可适用于该日期产品的优先/改单规则。可先用一个固定分钟的身份/事件衔接证据判门槛，不为找好结果改窗，也不直接拉两日L3整簿。这里仅提出最小获取条件，不授权请求或实现。

停止条件明确：若不能取得对应时段初态—事件链的可核接合，或优先规则仍只是猜测，则停止宣称“恢复真实队列/确定自己的成交”；保留现有候选与明确假设的条件情景，不靠扩大采样或私有后台无限追证。即使上述历史门槛通过，个人实时撤单可行动性仍需未来另行授权的实际时延/回执证据，不能由历史回放代替。

## 本轮依据与覆盖

只读8个本地文档：execution-20261022/root/两日挑战-最终结论.md；owner/parameters.json；owner/core.py（数据获取/解析与schema段）；owner/analysis.py（BBO/配对段）；maker-trade-previsibility-20261021/identity-time/FINDINGS.md；maker-cached-identity-time-20261021/FINDINGS.md；maker-raw-one-minute-qc-20261021/qc.json（字段计数段）；maker-fill-economics-boundary-20261021/matching/FINDINGS.md。源根为lobframe-data-entry-20261021；对应源码当前封存身份沿此前已验，无本轮执行。未读原始行情body/价格数组、未新统计、未联网（公开文档新增读取0/2）、无模型/回测/交易/修连接/保护Library访问；仅保存此文件。实际model/effort UNKNOWN；规则版本沿既有三项。

保存UTC：2026-10-22T02:34:08.858274+00:00

## 精准补充：May1固定短窗L3初态—事件来源门槛（未取行情）

本次只补读既有raw-catalog/exchange-metadata.json及已存官方实现/字段观察、July原请求回执；新公开读取0/2，未请求或读取May1新增行情。来源metadata原读取UTC2026-10-21 13:37:49–13:37:50；当前补读的是该保存对象，不宣称刷新当前覆盖。官方入口为https://api.tardis.dev/v1/exchanges/bitstamp ，本轮不重取。

**目录到底明示什么。** availableChannels列live_trades、diff_order_book、live_orders、funding_rate、ticker；btcusd为spot、availableSince2019-03-30。channelDetails.live_orders明确为Level3订单事件流，其additionalInfo明确：因WS订阅不给初始完整snapshot，供应商记录中包含来自REST API的generated初始盘口快照，包装为event=snapshot、channel=live_orders_<symbol>、generated=true。另一个diff_order_book也带REST生成snapshot，但其频道是diff_order_book_<symbol>，不能混作L3载体。目录没有单独名为REST或snapshot的可选channel。

**如何进入同一历史响应。** 按已核HTTP过滤格式，固定May1首分钟的拟定请求参数可为from=2026-05-01T00:00:00.000Z、offset=0、sliceSize=1、filters=[{"channel":"live_orders","symbols":["btcusd"]}]。它是一个尚未发送的参数规格；因为generated snapshot包装在live_orders_btcusd内，过滤该通道应同时保留该时段曾记录的snapshot与created/changed/deleted，不需要另加REST过滤项。现有May1 trades已存，可按原生两钟复用；如有另行明确理由把live_trades也放进同一filters数组，July既有一次实际成功URL已经证明这种双通道数组编码可正常返回。但最小增量不必重复下载现有trades。

这里from/offset是在历史采集记录中选时间片，**不是要求供应商现在为历史任意起点重新调用REST并制造当时snapshot**。文档目录未保证每个分钟、每个offset、每个10分钟请求开头都有新的初态；选offset=0亦不是实际存在初态的证明。May1该短窗是否含generated snapshot、全深度/字段、文件大小、hash、事件接合与覆盖仍均未取得；不把目录availableSince自动升级为该分钟已可重建。

**初始化与补链的已证/未证。** 已存Bitstamp官方字段观察（2026-10-21）记录GET order_book/{market_symbol}/group=2可返回不按价合并并含订单ID；live_orders有event_id/pre_event_id、断链/重启提示。July首分钟也实际有generated live_orders snapshot及第三列ID等值见证。因此有真实可检验的“初态+生命周期+事件链”入口线索，无需私人账户ack或XTX后台才能做标明假设的模型情景。

但目录未写generated L3具体取group=2、取得/封装时序或snapshot对应的精确event锚点；此前读到tardis-node的手动快照源码只实现diff_order_book/group=1，不能补证live_orders历史后台。July缓存的snapshot没有event_id/pre_event_id，其源钟早于紧邻前订单事件；仅在捕获行序插入快照再往后更新，不能当作已接合。May1必须就实际原件单独核：快照身份/字段，快照与先到事件如何接合，以及后续pre_event_id链连续；不能用July“看到过”填答案。

官方已存观察还记录公开order_data补漏最多1000条/次、事件保留30天（默认24小时不同于保留期）。它是近期WS补漏定义，不是2026-10-22补取May1的历史修复入口；当前REST order_book也只提供当前快照，不能初始化May1。Tardis的from/offset可选择**已经记录的历史片**，但不能自动填回历史缺事件。若固定短窗没有可核初态锚接或链断裂，就在该短窗停止“真实历史队列已恢复”的结论，不为了拼完整而无限扩窗/重试/调用当前REST。条件情景研究仍可单独定义，不要求先补成完美真实队列。

**有限成本依据。** 唯一已有同类实收参照是July1首分钟的混合live_orders+live_trades响应：压缩508,349B、解压6,711,520B，包含generated snapshot与12104订单事件；原始获取wall约2.34秒只是那一次环境。它只说明一个同类一分钟样本可能是压缩数十万字节、解压数百万字节的数量级，不能乘分钟数预填May1/两日大小，也不能保证live_orders单独一定更小或本次同样快。若未来另授权这一个来源门槛，可预先选单个固定分钟并设压缩/解压硬帽、一次GET；到帽/拒绝或缺可核衔接即停止，记录未知，不扩大为两日L3项目。

补充结论：**目录明示有live_orders内嵌REST-generated初态这条历史来源路线，July局部真实取得；May1此载体尚未取得、更未接合。** 这个差别是最小来源门槛，不能直接推为可以恢复自己的真实获单。读raw成交数量与补逐单初态/优先级是不同问题。

补充保存UTC：2026-10-22T02:39:39.642028+00:00
