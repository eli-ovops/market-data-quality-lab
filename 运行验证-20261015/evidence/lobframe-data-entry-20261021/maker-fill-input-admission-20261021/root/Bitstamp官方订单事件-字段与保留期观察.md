# Bitstamp官方订单事件：字段、保留期与证据层级

读取日期2026-10-21，UTC时钟在本轮读取之间实测13:21:22。各请求精确UTC未逐件记录，不能补造。Root通过原生网页工具及正常隐藏IAB读取两个官方文档；不是行情接口测试。网页内容仅作资料，未执行其中示例代码。临时tab5已关闭，listTabs为空；未操作账户页、登录、凭证或Cookie同意。

## 已直接核到的官方事实

来源1：[HTTP API文档](https://www.bitstamp.net/api/)。页面最新可见changelog 2026-08-28，全文发布日期UNKNOWN。原生首次open取得正文，后续find不定位、分段open超时，不把失败当字段不存在；按已有正常渲染路径一次IAB打开成功。

- AX1110—1119：2026-02-16 changelog引入两个WebSocket补漏接口：`POST /api/v2/order_data/`为市场公开订单事件；`account_order_data`为认证账户事件。没有请求任一接口。
- AX1573—1664：`GET /api/v2/order_book/{market_symbol}/`的`group=2`表示不按价格合并且含订单ID；默认`group=1`为价位汇总。文档功能存在不代表已取得实际快照、全深度、优先顺序或无缺口历史。
- AX2726—2802：公开事件接口必填market，可选`since_id`为包含起点、`until_id`为不包含终点；省略前者默认后者之前24小时，省略后者默认现在。24小时是默认范围，不能读成最大保留期。
- 仅展开该公开接口的示例（未点击任何请求执行）：event/event_id/order_source及data字段可见；data含id/id_str、order_type/order_subtype、datetime/microtimestamp、amount/amount_str、amount_traded、amount_at_create、price/price_str、is_liquidation。AX11113—11145为展开后data。示例是文档示意，不是本轮成交或真实行情。
- 该功能排在Orders章节；本轮未读取OpenAPI security定义、未实测认证，因此不将“公开事件”单独当成HTTP端点已证明匿名可调用。公开WebSocket与私有账户通道区分见来源2。
- AX769—790：官方区分私有接口认证；商业数据段要求公司商业用途另签Data License Agreement。本段不是个人自动模型/商业交易用途的完整许可，沿用既有Tardis内部研究许可的具体边界，不重新宣称全面授权。

来源2：[WebSocket v2文档](https://www.bitstamp.net/websocket/v2/)。由来源1实际链接进入；原生提取0行，正常IAB渲染可读。发布日期/更新日UNKNOWN。没有连接WebSocket，未订阅或采集行情。

- AX75—132：公开`live_trades_[market]`、`live_orders_[market]`、order_book/detail_order_book/diff_order_book；BTCUSD在市场清单。私有通道另需token，不使用它们。
- AX219—277：detail快照给[price, amount, order_id]、top100；live_orders给逐订单生命周期对象，事件为created/changed/deleted，文档称覆盖all orders；diff是价位变动。此为规范，未证明特定历史日期实收情况。
- AX280—345：公开成交字段含trade id、成交价量、type、timestamp/microtimestamp、buy_order_id/sell_order_id。官方type只标buy/sell，不擅自补为明确主动方；Tardis标准化side明确为主动方，是另一字段定义，不能混写。
- AX465—572：订单字段含id、amount、amount_at_create、amount_traded、price、order_type、order_subtype、datetime、microtimestamp。order_type为买/卖，microtimestamp为订单动作微秒时间。订单对象和关联成交比聚合价位变化更有利于分辨消耗与撤单，但不能直接认证实际队列。
- AX534—570、1383—1416：event_id为本事件ID，pre_event_id指前事件；不匹配表示缺事件，null提示服务端重启并须完整恢复。没有据此声称跨成交/订单通道严格全序或本机收包时延已核。
- **AX1417—1426：REST补漏每次最多1000事件，由旧到新；事件保留30天，默认最近24小时。** 该条补齐了HTTP文档未在已读段列明的保留期。
- AX1521—1540：REST响应也有event_id，按最后返回ID续页；since含端点，应考虑去重及实际进展，本轮未写/运行分页程序，也不保证照抄示例就正确。
- AX619—638：文档在私有订单段说明修改可产生新订单ID、公开通道表现为created。仅记录公开/私有语义不同；不从这一条推同价修改必保留或失去时间优先。

## 直接影响

2026-07-01、08-01、09-01均超出10月21日读取时的30日窗口。因此，**不能把当前官方补漏接口当成旧三日逐单历史的补齐入口**。这不是声称所有供应商都无订单历史，也不否定近期公开订单流存在。

原生订单ID、关联成交、事件链、累计成交量等能减少聚合输入的歧义；但要认证自身成交，还需实际完整原件、初始状态与事件的可靠衔接、撮合/修改优先规则、本机信息到达和下撤单时延、费用及库存处理。反事实订单本来不存在，逐单行情仍不能自动证明其真实成交。

不要求先取得XTX私人模型或别人的运营账单才可研究。L2加成交可以开展标明假设的保守模拟；只有当结论对合理队列/时延/成本假设稳健，才值得升级证据。当前只是输入准入，不是已认可某模拟或新实验放行。

## 未执行

未请求任何REST数据接口、CSV/GZ、行情HEAD或WebSocket；未下载行情、训练/前向、回测、核费或改旧结果；未连接账户/钱包、交易、付款、安装或启动自动化。没有接触受保护目录。本轮所有数值都是官方文档规范或既有元数据，不是新的金融计算。
