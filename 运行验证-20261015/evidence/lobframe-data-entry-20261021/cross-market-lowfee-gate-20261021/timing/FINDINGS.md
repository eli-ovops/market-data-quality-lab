# Lighter：普通账户短期跨市场时序准入

结论：官方文档表明确实给Standard较低的人工maker等待，但未能据本轮读取证明个人在500ms跨市场信号上保留净优势。公开行情通道的完整广播/时钟语义、研究及自动交易权限、同步历史数据尚未核全；当前只能有限文档准入，不能仅凭API存在判通过。

## 1. 人工延迟与真实到达/成交时延必须分开

[Account Types](https://apidocs.lighter.xyz/docs/account-types)已读L19–63（页面标updated 3 days ago）：Standard为默认retail/latency-insensitive类型，maker latency 0ms、taker latency 300ms、cancel/modify latency 300ms。它们是平台表列的人为等待，**不是端到端RTT或保证成交时间**；0ms maker不保证即时成交/排位，撤改单的300ms不能被新maker0ms替代。taker300ms也不能简单从预测500ms中相减得到“剩余200ms”：信号可能早已在传播中消散，且还有源行情到达、跨地网络、客户端计算、交易入队及确认。

本轮未取得平台对marketable limit/改价细分的完整排程解释，没有实测网络或总延迟分布。文档有Premium/Plus其他参数，但不是普通Standard同一权限条件；不以更高层级时延填入个人零费假设。费用/地区适用由另一Owner负责，本报告不认证个人资格。

## 2. 数据接入是有官方入口，不是已核完因果行情与研究许可

[WebSocket](https://apidocs.lighter.xyz/docs/websocket-reference)本次可读返回只覆盖L0–256/总1925，未覆盖后段公开Order Book/Trade订阅频道。已核其连接地址为`wss://mainnet.zklighter.elliot.ai/stream`，有只读参数说明；没有连接或请求payload。L40–52要求客户端至少每两分钟发送一个frame，掉队读消息可能断线。该保活要求不是行情广播间隔，也不是成交延迟。

已读Transaction/Order/Trade schema列出timestamp、transaction_time、queued_at/executed_at及block_height等字段，但此范围未明确单位、交易所事件/撮合/块/采集接收时间的精确定义；不能仅凭字段名和样例位数声称已经建立可比时钟。公开盘口/成交频道是否无鉴权、广播频率与snapshot/delta连续性、深度/丢包恢复，均在本Owner未覆盖部分，保持UNKNOWN。账户私有/下单鉴权与公开行情鉴权也不混同。

文档公开可读、提供只读入口，尚不是对历史存档、研究用途、再分发或Standard自动交易的完整权利授权。本轮未取得禁止或明确允许Standard自动交易的条款；不能从速率限额反推许可。未核到一份带共同接收时钟的Lighter＋领先市场历史数据档案，其可得性/权利UNKNOWN。这些UNKNOWN不是数据不存在或平台禁止研究的结论。Root独立预算若补取未覆盖内容，须另列补证，不追认本Owner已读。

## 3. 速率可读但不能换算成稳定反应能力

[Rate Limits](https://apidocs.lighter.xyz/docs/rate-limits)（updated 5 days ago）列Standard REST为60 requests/rolling minute；Standard送单仍受60/min限制，WS sendTx/sendTxBatch不因改传输方式获得豁免。另有按交易类型的限制，不能假设每种操作都能耗尽60次。滚动分钟上限不是强制逐秒间隔，也不证明可持续高频撤改或每个消息都成交。

WebSocket每IP最多255连接、每连接500订阅、每IP5000订阅；客户端每分钟200条消息，最大inflight50，sendTx类另计。这些是连接/订阅/客户端发送额度，**不是服务器行情推送速率**。超限可能HTTP429/405或断线，REST/WS限流互相关联。未做任何压测/连接，个人真实吞吐和丢包表现UNKNOWN。

对500ms假设的处分：可确认需要显式建模Standard taker及cancel/modify人工等待，不能照搬零延迟回放；maker路径也仍需成交与撤单风险证据。现阶段未满足“源市场输入何时本地可知→Lighter随后反应→个人能按可执行价格进入/退出”的时序闭环，因此不判个人净优势通过，也不据300ms数字直接否定所有500ms信号。

## 读取回执与未核范围

只读公共资源7项（一次搜索调用内2个定向query，另6页面请求）：搜索；docs.lighter.xyz根；apidocs.lighter.xyz根（转systemConfig文档）；docs.lighter.xyz/llms.txt；account-types；websocket-reference；rate-limits。索引精确URL仅工具不可访问、源HTTP UNKNOWN；查询LOCAL_BLOCKERS后停止该路径，无重试/镜像/代理/身份切换。没有读取任何API行情数据，systemConfig只读文档，没有点Try It。

本轮公开文本读取日UTC2026-10-21；原返回汇总封存时刻UTC2026-10-21 09:33:12，逐请求精确秒数未留，UNKNOWN，不将工具Crawled日期冒作请求时刻。原返回见四份native.txt，均是工具提取文本，不是raw HTTP响应。所读范围明示到行，未声称完整读取1925行WebSocket。费用/地区条款、法律授权、历史数据与广播后段不在已完成核验范围。

规则PERMISSIONS-2026-10-14-v1 / ROUTING-2026-10-13-v4 / HANDOFF-2026-10-10-v2沿用；目标gpt-6.1-sol/medium，实际model/effort UNKNOWN。无源码执行、网络行情连接、登录/钱包/签名、模型/回测/交易/安装/付款/外发，旧STOP不变。未接触禁止目录。
