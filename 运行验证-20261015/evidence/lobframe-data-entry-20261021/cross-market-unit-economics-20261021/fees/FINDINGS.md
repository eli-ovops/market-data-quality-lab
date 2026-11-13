# Bitstamp BTC/USD 现货费用：当前数字未核得

日期2026-10-21。仅公开文本研究，无账户、私人API、行情或计算实验。实际model/effort UNKNOWN；规则沿PERMISSIONS-2026-10-14-v1、ROUTING-2026-10-13-v4、HANDOFF-2026-10-10-v2。

1. **当前普通小额用户maker/taker基档与零费例外均UNKNOWN，不能给具体经济门槛贴“真实费率”标签。** [当前官方费表](https://www.bitstamp.net/fee-schedule/)本轮原生读取0行；HTTP原状态及正文UNKNOWN。按既有正常渲染先例尝试CUA，返回Browser is not available: iab，当前listBrowsers为空；未换身份、代理或浏览器。故当前BTC/USD spot具体费率、每次执行按成交名义额计费的准确规则、分档阈值、rolling窗口及跨档时点未取得现行原文。旧每边25bp或其他成本数只能保留为假设，不能写成用户真实费用。

2. **官方旧公告只证明历史制度，不能证明当前零费。** [2022-08-18公告](https://blog.bitstamp.net/post/bitstamps-summer-of-discovery-is-underway-with-0-trading-fee-for-all-coins/)说明maker提供流动性、taker即时取走流动性，并记载此前30日rolling总交易量至1,000 USD可零费；[2023-03-30应用公告](https://blog.bitstamp.net/post/meet-the-new-bitstamp-apps-for-android/)也记载该门槛。即使旧文说长期保留，也不能代替2026现费表。限价单是否maker取决于实际提供/取走流动性，不能仅按订单名称给费率；本轮没有新增成交检验。

3. **费用和用户资格层仍须分开。** 地区/法人、实际客户等级、活动有效期、BTC/USD准确现行适用及全样本历史费率UNKNOWN；公开基档即使取得，也仅能构成情景，不能证明用户准入或账户费用。官方API文档搜索结果的maker=0.15000、taker=0.16000是Response samples，本轮未调用接口，不能当真费率。资金划转、入出金、滑点等费用外项未补核；报价预测分数不等于扣费净利。本候选Kraken仅为信号输入，本轮没有查其交易费。

读取范围：1次费表页面、3条定向官方搜索查询，共4个公开来源对象；另1次CUA创建失败（未取得页面）和1次浏览器清单。先按LOCAL_BLOCKERS既有Bitstamp条目与失败信息定向核查，无明确源403/认证，也未追加旧HTTP防护页或反复请求。未访问受保护Library路径。
