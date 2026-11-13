# Bitstamp同期历史成交与盘口：能支持哪一层

2026-10-21，只读复用既有官方metadata及字段原文，新增公开对象0/6。实际model/effort UNKNOWN；沿现有规则与研究权限。没有请求数据API、CSV/GZ、HEAD或读取已有行情体，没有训练/模拟执行。

1. **目录列有trades与incremental_book_L2，尚未列出逐单事件数据。** `cross-market-independent-plan-20261021/data/metadata-receipt.json`保存本日10:51:18.946006—10:51:24.486119UTC官方[Bitstamp覆盖metadata](https://api.tardis.dev/v1/exchanges/bitstamp)记录：spot原生`btcusd`、CSV `BTCUSD`；2019-03-30至2026-10-21，dataTypes包含trades、incremental_book_L2、quotes、book_snapshot_5/25。因此2026年1—9月首日，尤其7/8/9月1日均在目录范围内；不是实际逐日文件可达/无缺口证明。该CSV清单没有L3/逐订单事件类型；不能据此否定未经本轮核查的原生历史通道。已有快照文件不等于同期trades/增量文件已经取得，本轮二者均未取。

2. **字段可支持成交方向与聚合盘口重建，不能识别每笔撤单或自身队列。** 依据已保存[官方Data Types](https://docs.tardis.dev/downloadable-csv-files/data-types.md)原文`root/data-types.native.txt`：

| 字段/语义 | 已核文档事实 | 实际文件/限制 |
| --- | --- | --- |
| trades side | 流动性taker/aggressor视角；buy、sell、unknown | Bitstamp各日实际填充率UNKNOWN，不是maker侧 |
| trades id | 交易所提供的trade ID，源无ID可空 | 不是订单ID；Bitstamp实际唯一性/缺失UNKNOWN |
| trades price/amount | 成交价/量 | 非挂单量、个人成交或费用 |
| timestamp | 交易所epoch微秒，缺失回退local_timestamp；UTC | 是否回退及源时钟误差UNKNOWN |
| local_timestamp | 供应商消息到达epoch微秒 | 不是个人收包/成交时间，不证明跨通道严格总序 |
| L2 side/price/amount | bid/ask价位的更新后总量，非delta；0删价位 | 不带订单ID、事件类型或撤单原因 |
| L2 is_snapshot | 初始快照标志；重启新快照须清旧状态；首快照前增量跳过 | 不能当全量断连/丢包证明 |
| L2消息分组 | 同local_timestamp可按文档归组多价位更新 | 不等于每个交易所订单事件都有一行 |

L2减少可能混有成交、取消/修改及聚合发布；trades提供发生的成交量线索，但缺订单级关联、完整序号/原子先后、隐藏量与个人订单位置，不能严格逐笔拆分消耗和撤单。仅凭这些输入不能恢复自身真实FIFO队列或证明某挂单本可成交。可研究聚合盘口/成交驱动的、显式假设下的模拟fill；这不是实际成交重建，模拟是否可信仍未验。

3. **免费与ML许可有既有依据，不能扩大为无限数据或执行许可。** 旧冻结方案L27—29引用Bitstamp月首免key说明；当前被拒的Bitstamp文档和旧overview.md未重取。月首制度不代表任意日期免费，具体文件/大小/完整性UNKNOWN。已有本日正常读取的Tardis2026-10-20条款§9.5允许相应内部AI辅助与仅Customer Users使用的自建模型；§9.4持续许可仍受§10.5及上游限制，模型/数据外部分发不由此获准。该一般许可不证明所有上游链已核，亦不授权本轮实验。此处不重复许可检索、不将Coinbase专门禁令套到Bitstamp。

原件范围：上述小metadata回执、`cross-market-paired-data-admission-20261021/root/data-types.native.txt`的L21—46及L124—139、既有rights与冻结方案。精确字段事实是规范层；未补造Bitstamp具体文件非空率、逐单事件可用性、用户队列或实际手续费。Root另核官方live_orders/REST定义，不与其混作已收历史数据。
