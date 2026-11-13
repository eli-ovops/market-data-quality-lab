# 数量单位窄补证：不更改已完成QC

结论：当前原文支持Tardis传递交易所原生数量、Bitstamp mapper不另作量缩放；**本次有限范围仍未取得明示BTCUSD raw trade amount与snapshot amount均以BTC计的精确官方句子**。不凭价格/量值或spot常识把它升级为已认证。方案可继续把两者同为BTC列为明确模型假设，不能标成已核单位事实；不必为此扩市场/账号/L3。

既存官方Data Types保存文本：incremental L2 amount为交易所提供的价位更新后总量，非delta（工具L46）；trades amount为交易所提供的成交量（L139）；snapshot25为重建价位量（L64/77）。这些定义没有给当前Bitstamp对的币种单位。

新读取1：https://docs.tardis.dev/faq/data.md ，UTC2026-10-22 03:07:35–03:08:02，正常text/plain，356行文档，工具实际返回覆盖L0–280。L35–39/L90–95说明raw保持交易所原格式，统一格式映射公开；L218–225只说明衍生品量可能是contract/base/USD，不能把衍生品公式挪给该spot对。没有本对的BTC单位明文。未读取链接行情示例、被拒Bitstamp专页或overview。

新读取2：https://github.com/tardis-dev/tardis-node/blob/master/src/mappers/bitstamp.ts ，UTC03:08:13–03:08:15，正常源码页面，显示293源码行。工具正文L830–860：trade price/amount直接Number原值，type0映射buy。L1033–35、1134–36将bids/asks送入_mapBookLevel；L1146–52把level[0]/[1]直接Number变成price/amount，没有数量缩放或币种换算。这是官方客户端实现证据，支持“保留原生数量尺度”；它没有给两个原生字段的物理单位起名。master未固定commit、发布日期UNKNOWN；本轮不追加取HEAD、Raw或历史部署追查，不要求私有后台证明作为条件模型门槛。

精确短片段（该源码合计少于25英文词）：
`amount: Number(bitstampTrade.amount)`
`const amount = Number(level[1])`

本窄补证用满2个官方对象，0行情请求、搜索、登录/凭证、安装或模型/PnL；原QC脚本/summary/receipt完全不改，未重算旧D。源格式微秒和本前缀实际1000µs格仍分别成立，均不认证时钟准确度。实际model/effort UNKNOWN。
