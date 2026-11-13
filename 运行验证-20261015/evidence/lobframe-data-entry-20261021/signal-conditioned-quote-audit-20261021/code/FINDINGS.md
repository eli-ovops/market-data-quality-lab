# signal-conditioned quoting / mm_pnl：固定代码静态核验

结论：已读代码实现了“用当前记录的盘口imbalance决定保留哪侧报价”，并提供模拟填单/费用分解；没有核到真实队列、订单确认或到账回执。signal对照与后续对称queue研究是不同问题，不能混用正结果。全部结论仅限固定commit `1644347871bb568a614ba9a6a9634c224dc6799b`；没有运行、测试、模型加载、回测、原始数据或数组读取。

读取：复用Root完整461-entry tree及既有认证状态，gh官方API固定blob共4/4。保存src/mm_pnl.py、src/mm_queue_study.py、src/orderflow_study.py、app/venue_fees.py原文本，未取HEAD/tree。复用Root已保存preregistration与2026-10-12 update文字，无额外网络。GitHub skill已读取并沿用。没有访问凭证内容、改变认证、账户或交易；旧STOP保持。

## 1. signal是同点盘口阈值过滤；有每fill比较，但没有充分控制“少交易”，queue主测试没有启用它

[mm_pnl quote_sides L245–281](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L245)：默认threshold=.65；imbalance≥.65保留bid、撤ask，≤.35保留ask、撤bid，中间双边。lean更极端时才撤危险侧（默认边界.825/.175），symmetric一直双边。这里不是拟合出的概率模型，也没有把未来mid/未来markout传入quote_sides。compute_quotes给出基础报价后再按此布尔门控；本轮未读其被调模块，报价公式/库存cap的完整实现UNKNOWN。

[run_token L498–571](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L498)先用此前报价检查本区间填单，再用当前point.mid/spread/imbalance与已模拟库存决定下一报价。queue版同样先处理prints/既有订单再做当前决定。未来mid只用于事后markout/终值评价，在已读决策路径未见它直接成为signal输入。

但输入因果时钟未闭合：[orderflow loader L218–310](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/orderflow_study.py#L218)直接读取CSV imbalance_top，不在此重算；book优先recv_ts，tape优先trade_ts、再exchange_ts/recv_ts，不能凭排序证明行情和成交采用同一接收时钟。其模块说明称imbalance为top-N美元深度bid占比，实际producer算法、N、字段生成时间及原数据正确性本轮未读，均不冒充已核。

[quote_mode_comparison L815–841](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L815)在同一数据/基础参数/填单模型下分别运行三种模式，报告fills、总额、markout/fill与日CI。其注释明确少交易会使总亏损缩小，故看每fill markout。这比只看总额更有信息；但不同模式改变成交侧/时点、库存与后续报价，没有等成交量随机过滤或同风险暴露对照，单靠每fill改善也不能识别纯信号因果增量。没有以本次静态读取重算或认证任何公布结果。

[mm_queue_study run_day L63起](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_queue_study.py#L63)调用run_experiment没有传quote_mode，后者默认symmetric。因此queue候选/训练选择并非signal增量验证。预注册明确研究对称做市，引用PR#148；当前commit是否等于9月当时实际评分实现，及外链pmt-mm-research原研究/输入/代码身份，本轮未取得绑定证据，保持UNKNOWN，不能从同文件名推定同版本。

## 2. touch/tape是不同填单假设，不是实测上下界；queue加了深度与部分成交，仍未取得真实排队证据

[touch_fills / tape_fills L284–319](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L284)：touch在下一snapshot的opposite touch穿过我方旧报价时记整笔成交；tape按taker方向及print穿价记成交，每侧每区间最多一次。run_token按quote_usd/price设置整笔shares，不检查该print量是否足够，不记部分成交，tape也将填单时间统一记为区间末point.ts。两者忽略真实队列；所谓悲观/乐观是模型描述，不能据此证明真实成交数量或净利润必在两者之间。

[queue_fills / refresh_queue L407–474](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L407)：同价print先消耗假设queue_ahead，再部分填我方；穿过更差价时视作本级已扫空。可见档加入已有量之后；看不见档front假设空、back待见；非print深度减少front归队前撤单，back不作同样减法，但会将queue_ahead裁至可见剩余量。保持价格保留队列和剩余量，改价重排。它是从L2/公共tape推断，不是本方订单排位观测。

[run_token_queue L575–695](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L575)只在queue路径应用latency_s；pending生效前旧单仍在，期间新决定可被丢弃。激活时用pending中保存的决策时depth初始化队列，未重建到达瞬间全量盘口。touch/tape分支没有接收latency_s，所以传了该参数不代表所有填单模型都应用延迟。250ms是设定情景，非已测订单延迟。

另一个需要保留的条件性实现风险：[L477–487](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L477)的区间查询含start与end两端。若某print时间恰好等于相邻snapshot共同边界，它可在相邻两区间再次进入处理；是否造成重复成交取决于当时订单/剩余量，发生率及对结果影响未读数据量化，不能说所有运行一定受影响。

Root已存2026-10-12 update也明言实际队列、fills及quote activation未由自己live orders核验。该文报告对称queue测试0ms正、250ms负，且0ms去假设rebate仍正；不能抹掉这个模型内正证据，也不能将其升级为实盘或signal过滤收益。

## 3. 总损益是终端mark-to-mid恒等式，费用确有接线；“spread/5min markout”命名需要按实际参考价解读

[MMFill L120–165及Decomposition L168–216](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L120)实现：signed_shares×(mid_final−price)拆成capture、markout和late drift，再加rebate减fee。**不是完全没扣费**。但[mid_at_fill传值L548、633](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L548)实际为quote_mid，即决定该报价时的mid，不是成交当刻mid。因此capture实际为相对报价时mid的价差，markout也包含从报价至成交的等待漂移；不能把该列当严格“成交时mid→成交后5min”的不利选择估计。该参考价移动不会破坏三项之和等于终端mark-to-mid的代数恒等式，却会改变归因含义。

_markout取成交时间+300s后首个snapshot，允许再晚≤300s；若无合格未来mid，markout置0并把剩余漂移纳入late_drift。touch/tape的成交时间又是区间末，所以其窗口不是实际print后精确300秒。mid_final为每token所装载序列最后mid，没有代码证明可按该价平仓；queue_study逐日加载、每天库存从0开始，末仓按末mid估值，不是连续现金/库存账户。

[decompose L700–731](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/src/mm_pnl.py#L700)对Polymarket累加maker rebate、maker fee不另扣；[venue_fees L160–172](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/app/venue_fees.py#L160)按shares×category rate×p(1−p)×默认15%估算返佣，函数说明为分配上界近似、实际日分配可能更低。这不是到账记录或本轮核实的现行官方费率。decompose虽有Kalshi分支，但run_experiment没有传venue、默认Polymarket；本轮不扩展其他策略/场所。

总额没有强制清仓费用/可执行退出价、全token共用资金预算或真实资金流回执；各token独立从0库存开始。流动性奖励在run_study另列total_with_rewards，不应与decomposition.total_usd混成同一个收益数字。其底层奖励实现未读，不认证实际可得性。

结论处分：可以保留“signal门控/每fill诊断/queue假设及PnL恒等分解”的静态研究方法；当前没有证据把signal-conditioned报价判为已证实净赚钱环节，更没有用对称queue的模型内正值代替该增量证明。只收口代码审阅，不发起运行、修复或新交易。

## 范围与原件

已完整读取mm_queue_study及必要mm_pnl决策/填单/聚合/比较/划分/输出限制函数，orderflow只读输入结构和loaders，venue_fees只用于maker费返佣链。未读compute_quotes模块正文、记录器producer、真实orders/confirmations、原始行情、外部pmt-mm-research实现和9月原执行环境，也没运行测试。四份源码保存原文不作修改；未把文中注释或预注册自述当外部执行证据。Root负责研究md结果与许可，本Owner没有重复公共读取。

目标gpt-6.1-sol/medium；实际model/effort UNKNOWN。规则PERMISSIONS-2026-10-14-v1 / ROUTING-2026-10-13-v4沿用。公开blob读取4/4；付款、安装、数据下载、源码执行、模型、回测、账户和交易0。
