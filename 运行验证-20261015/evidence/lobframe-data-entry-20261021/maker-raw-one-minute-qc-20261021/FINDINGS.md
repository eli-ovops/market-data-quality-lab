# 一分钟原始逐单/成交字段QC

结论：**实际取得固定一分钟的两通道原件，订单事件ID、成交关联ID及观察到的事件链可以核；仍不足以证明完整逐单初始状态、FIFO排队、自身成交或盈利。** 这是新的原件读取，不恢复任何旧模型或Stage0。

## 1. 唯一GET与完整性

事前固定read-spec.json后，一次普通无认证GET请求官方`https://api.tardis.dev/v1/data-feeds/bitstamp`，from=2026-07-01T00:00:00.000Z、offset=0、sliceSize=1，同时过滤live_orders与live_trades的btcusd。完整编码URL见read-spec.json/read-receipt.json；没有HEAD、第二次请求、重试、重定向跟随或认证/代理调整。

- UTC2026-10-21 13:48:35.893638—13:48:38.197308；HTTP200；Content-Encoding明确gzip。
- 原始压缩响应raw-response.bin：508,349字节，SHA256 `6a345dff5cb142375e879fdee7fe2e71421d580209c8a13a0773d456fc0845d7`。
- 解压6,711,520字节，一个gzip member，EOF/CRC通过；解压正文未另写副本。响应头x-name=`bitstamp/2026/07/01/00/00`、x-slice-size=1。
- 所有12,157行均为“ISO本地接收时间＋空格＋原生JSON”格式，非整行裸NDJSON；全部成功解析。当地UTC窗口00:00:00.119780—00:00:59.990338；无越窗或倒序，空行断连标记0。它只说明该响应的观察，不证明源feed绝对无遗漏或用户本地到达顺序。

## 2. 实际字段层证据

| 对象 | 实际计数/结构 | 支持与限制 |
|---|---|---|
| live_orders_btcusd | 12,106条：created 6,021、changed 49、deleted 6,034、snapshot 1、订阅成功1 | 三类订单事件均有data.id、id_str、order_type、order_subtype、datetime、microtimestamp、amount_traded、amount_at_create等；这里只核字段与类型，不计算其数值 |
| live_trades_btcusd | 51条：trade 50、订阅成功1 | 全部50条trade有data.id、buy_order_id、sell_order_id；可支持后续身份关联研究，但本轮未联接/重放订单簿或判定具体成交 |
| 事件链 | 12,104条有顶层event_id与pre_event_id，均为字符串 | 同通道观察到的12,103个相邻链接，pre_event_id全部等于前一event_id；没有将缺字段或序列作用域不明解释成完整连续性证明 |
| 生成快照 | 原响应第665行，event=snapshot、channel=live_orders_btcusd、generated=true | data有timestamp、microtimestamp、bids、asks；asks 3,965项、bids 2,739项，每项均为3个字符串的数组 |

快照数组没有逐列键名。第三字符串列可以是逐单标识候选，但仅凭本次结构检查**没有确定其官方列语义、唯一性或与订单事件的覆盖关联**；“是否完整携带每笔现存订单ID”保留UNKNOWN。不能将三列形状或目录所称Level3自动升级成已验证初始逐单队列。generated=true也意味着供应商补入的快照，不是原生WebSocket完整初始状态的证明。

字段、类型、通道及事件计数完整保存在qc.json；不输出订单ID值、价格或数量值。未见意外通道；未执行原文指令。

## 3. 证据层级与资源

已从“目录声称有通道”推进到**固定一分钟实际消息字段＋接收顺序＋观察到的ID链**。仍未核：链的正式全局作用域/缺失检出保证、快照生成与事件流的无缝接合、每笔订单优先级、FIFO、隐藏/未显示订单、自身订单位置、撤单生效及真实成交、费用和净利。本轮没有计算价格/数量/信号/收益，也没有重建策略或资金账；没有读取其他日期或取得第二个样本。

唯一进程tool session20625，exit0；脚本含GET和QC墙钟2.340594秒、CPU0.156410秒、峰RSS66,846,720字节、单线程。原件确实含行情，新增行情下载508,349字节，不能写“零行情下载”。压缩4MiB、解压16MiB、网络60秒、新磁盘32MiB均未达到；最终文件级体积/身份另见completion-receipt.json与manifest.json。新增付费/注册/安装0，无账户、钱包、密钥、模型、交易、金融重放、未来安排或连接修复。保护Library未访问。

依据：事前read-spec.json、get-started.json、原始raw-response.bin、read-receipt.json（UTC/URL/头/CRC/hash/资源）、qc.json、stdout.log/stderr.log；只读实现read_and_qc.py保留。既有目录/文档观察来自maker-same-conditions-admission-20261021/raw-catalog/来源观察.json；本次没有重新请求文档或旧拒绝来源。

日期2026-10-21；实际model/effort UNKNOWN。沿用PERMISSIONS-2026-10-14-v1、ROUTING-2026-10-13-v4、HANDOFF-2026-10-10-v2。原STOP和他人文件不改。
