# HftBacktest复用适配审阅：仅局部可借，默认完整引擎不可直接替换

2026-10-22，只读新增证据；未安装、导入/执行来源代码、benchmark、取行情或金融核算，不修改已审方案。结论是**仅局部可借**：成熟实现可提供队前量/partial fill/订单状态的参照和MIT可复用代码；直接选择内建队列＋PartialFillExchange会改变当前固定F/H模型。现有缓存可继续作明确模型输入，不必先补连续L2/L3才能研究；不能把它认证成完整真实回放。

## 1. 现成组件确实有，但默认行为和固定方案有实质差异

本次沿用已存官方固定commit `5f3ec40b2afb764e0fea112f941ed85523ef4e88`（提交author时间2025-12-23T15:31:05Z），不以latest网页替代。三个实际blob在sources/保存为惰性Rust文本，并验证Git blob身份。没有执行或编译。

|组件|固定实现事实|与已审模型关系|
|---|---|---|
|RiskAdverseQueueModel|接受时同价显示量初始化a；trade减qty；depth把a钳到min(a,new_qty)；is_filled将负a按lot_size四舍五入为可执行量，再置a=0|“初始化可见量、只按同价交易消耗”的核心可借；**depth钳位不能原样照用**，因为盘口减量会缩短a。它并非本方案“不从盘口减量获得队前进收益”。f64/lot rounding也不同于拟议Decimal BTC。|
|PartialFillExchange同价部分成交|同价trade先更新queue，再取可执行量与leaves_qty较小者，更新剩余量及PartiallyFilled/Filled|部分成交和剩余量记账有现成参照。实际状态/fee apply_fill实现未读，不称完整现金预留/现货风险已认证。|
|PartialFillExchange其他填单路径|sell价低于buy print、buy价高于sell print会整单fill；best bid/ask越过己方挂价也会整单fill|**不符合固定方案**：后者仅同价且方向相容的打印量消耗，不凭穿价/碰价自动fill。仅换QueueModel无法关闭这些exchange路径。|
|GTX/post-only、cancel/modify|GTX到所时可跨价会Expired；ack_cancel在处理时才删活跃订单；部分modify会cancel+new重设队列|有订单生命周期骨架；当前方案“所有改价撤后再挂、等待取消、TTL1秒、两情景、库存预留”等仍需策略/适配层明确实现，不能把GTX一个选项当整份规格。|
|ConstantLatency|分别返回固定entry_latency和response_latency，单位须与数据一致；exchange处理接收队列中的New/Cancel/Replace再respond|可表达固定常数延迟，不证明个人网络/撮合时延。local订单总线和完整调度器本轮未读，不能认证其同戳排序、响应是否多算一腿或与本方案capture代表点同构。|

固定行链接：[queue new/trade/depth/is_filled L63–95](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/hftbacktest/src/backtest/models/queue.rs#L63-L95)；[同价及穿价fill L128–244](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/hftbacktest/src/backtest/proc/partialfillexchange.rs#L128-L244)；[best变动fill L291–384](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/hftbacktest/src/backtest/proc/partialfillexchange.rs#L291-L384)；[GTX/新单初始化 L387–491](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/hftbacktest/src/backtest/proc/partialfillexchange.rs#L387-L491)；[cancel/modify L654–731](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/hftbacktest/src/backtest/proc/partialfillexchange.rs#L654-L731)；[订单接收处理 L827–852](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/hftbacktest/src/backtest/proc/partialfillexchange.rs#L827-L852)；[ConstantLatency L13–54](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/hftbacktest/src/backtest/models/latency.rs#L13-L54)。

以上差异只说明**与已固定协议不一致**，不判成熟引擎无效或虚增收益；例如a=min(a,new_qty)在其完整盘口估计模型中有自己的约束理由，当前稀疏snapshot25不能认证它对应实际队列演变。ConstantLatency明确只要求单位一致并建议纳秒；不是替任意输入自动识别单位。未来适配必须固定原native/CSV时钟到引擎整数单位的映射、精度和溢出规则，本轮未核转换器，不猜某未读转换链实际用ns或µs。

## 2. 缓存并非可直接喂入的完整引擎行情；也不能说引擎只准连续diff

已存官方Data/DataPreparation说明是带ev/exch_ts/local_ts/px/qty/order_id等字段的标准化事件，建议tick-by-tick full book＋trade。这里复用的是2026-10-18取得的官方页面文本，网页版本未绑定上述commit；不把它与源码混成逐字同版本证明。

本次固定源码进一步明确：exchange.process既接DEPTH_EVENT，也接DEPTH_SNAPSHOT_EVENT和CLEAR，再逐档update并调用queue.depth和best更新逻辑。因此**接口确实容许snapshot，并没有“语法上必须只用diff”的结论**。[处理L743–821](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/hftbacktest/src/backtest/proc/partialfillexchange.rs#L743-L821)。

但当前snapshot25只是两侧有限档位的观测，raw prints提供发生过的交易量，不能恢复快照之间漏掉的depth变动、订单优先级或25档之外状态。两快照相减不能伪造为完整真实L2 diff；离开25档不等于已知真实撤单为0。原样生成snapshot/clear输入虽可能在接口上成立，仍需定义top25替换、档外未知及排序；默认best更新和queue钳位会产生第1项的不同成交。那是**另一个模型**，不是无需修改的固定方案。

对本方案，足够的最低输入仍是现有缓存的as-of快照＋原raw同价打印量：接受时读可见a，活跃后只按合格打印消耗；不用伪造连续diff。这能定义有限模型，不能升级为真实队列或本人获单。normalized没有amount，而原raw有；若未来实施必须用原raw Decimal量，不能用一笔=一单位补量。本轮没有打开这些行情body。

## 3. 可商业复用的是软件许可；最低成本是局部复用，而非引入完整默认引擎

已存根LICENSE全文本轮复核，Git blob `28c446419cb8488ff0825fabb0954bc4d6e8fda1`，MIT，允许使用、修改、分发、再许可、商业复制；复制或实质复用须保留版权及许可通知，无担保。[固定LICENSE](https://github.com/nkaz001/hftbacktest/blob/5f3ec40b2afb764e0fea112f941ed85523ef4e88/LICENSE)。所以本次所读Rust模块有明确个人/商业软件复用依据，不存在LOBFrame NC许可的同类限制。未读全部依赖许可、另列py-hftbacktest/LICENSE或包发行工件，不能宣称整个二进制依赖链法律审计已完成。

MIT不授予Bitstamp/Tardis行情权利、个人交易准入或实际费率。旧HftBacktest样本仅2024-08-08末约344.8秒，非本两日；旧collector样本许可/来源缺口与新repo示例根许可判断仍分开。支持者reach.stratosphere.capital有TLS主机名错误，本次没有重试、关闭TLS或换源读取它。当前既有Tardis两日原件不因换引擎而扩权或获新执行许可。

**明确选择：只局部借用审过的成熟机制，保持固定模型。** 队前量初始化、按同价qty消耗、min(可执行量,剩余量)、partial状态与取消后释放/重排队的设计可作为小适配的可审参照；任何实质源码复用附MIT。必须显式去掉depth钳位进队、禁止穿价/best自动fill，保留当前Decimal、source/capture guard、同戳代表排序、现金库存约束和终端规则。此处是复用判断，未写实现。

采用完整引擎则不仅需格式转换：至少自定义QueueModel＋exchange fill路径，并核local/entry/response调度和数量/费用精度，还要写同样的F/H策略、风险/预留、未知及终端适配。**本轮静态证据下它不是最低成本的直接替换**；没有benchmark，不虚报节省多少时间。不能为减少开发而悄悄采纳默认fill改变固定检验。

唯一后续只读验收点已具体：未来实现设计若引用这些组件，对照“默认行为→禁用/保留”的表逐项绑定；无需先安装引擎或增取数据。是否实际开发/核算仍待新的具体单元范围，本报告不启动。

## 读取回执和未核范围

本轮公共内容4次：gh code search 1＋固定queue/partial/latency blob各1，均CLI exit0。skill要求的gh auth status已核，只报告状态、不保存凭证。三个API响应及惰性源码、Git blob和SHA256见source-receipt.json；逐请求精确开始UTC未捕获，只保留读取日和接收后UTC，不伪造HTTP头/实测耗时。

完整阅读本次相关实现：RiskAdverse四方法、ConstantLatency、partial同价/穿价检查、fill、depth/best变化、GTX及新单、cancel/modify和process/recv分支。未审概率/L3 queue全体、所有asset/fee/state、订单总线、reader/depth完整实现、安装版本/运行兼容/速度及真实账户结果。未取得完整L2/L3，也不声称这些不存在。

复用旧证据：hft-example-record-audit-20261021/records/FINDINGS.md及tree；HftBacktest-dual-clock-data-admission-20261018/publisher/{audit.md,native-documents-and-attempts.json}；HftBacktest-own-sample-permission-20261018/publisher/{migration-complete-tree-addendum.md,migration-newrepo-LICENSE.inert.txt}；HftBacktest-continuous-history-source-20261018/publisher/source-audit.md；小样本根结论仅定位用途，不读payload。原件均保持。

仅本独占reuse-engine-review写文本/JSON源码证据，未改固定方案、执行结果或任何旧STOP，未访问保护Library。实际model/effort UNKNOWN；规则PERMISSIONS-2026-10-14-v1、ROUTING-2026-10-13-v4、HANDOFF-2026-10-10-v2。0付费/安装/模型/回测/交易；代码文本读取不是行情下载。
