# 精确同窗标签诊断：正式前独立静态审阅

UTC2026-10-22 11:53:21。**READY_WITH_LIMITS；must_fix=[]**。尚未看新同窗数值，未执行合成、coverage扫描、标签聚合或bootstrap。实际model/effort/speed UNKNOWN。Root仍须按已审seal release后才唯一formal。

绑定seal SHA256 `a9fb072a9b6c646f1463c5a0f9f0280449ad1db8c435bc445bb88e965a5c64a0`，详见`version-binding.json`。本地aggregate/synthetic/spec、12项合成回执与seal hash匹配，授权及旧manifest/analysis/参数/两summary小文件身份匹配。未读取coverage正文或独立hash其大文件；其完整压缩SHA/EOF/CRC事前固定于唯一正式读取检查。

## 实质检查

- **精确窗口与原选择不变。** 完整读aggregate.py 155行。L89–93检查原capture→grid映射及合格label存在性；L118同时建窗口5..32449和原全天5..86394的独立累加器。L31–45先保留窗内全部row分母/状态/原因，再仅对原selected_first、原qualified label及hint==passive_side入cell；没有choose_first、补后来ID、生成新label或调用原analysis。最后一格原闭端观察至09:00:50，边界并未误截。原buy/sell orderID分别用于其被动侧distinct ID计数，原不同未知/无提示/零分不进入loss时仍保留在分母。
- **原权重与19块适配落地。** L47–53同格math.fsum/订单数，再各cell对有效格等权、买卖各半D；四cell一空D=None。每块保存格均值sum/count，不平均块D。L57–70单rng20261021，1999复制每rep先May19再June19，抽0..18、联合4cell；逐日四cell均非空才有效，分别≥1900给type7区间；辅助两日仅同rep双日有效、也需1900。19块含首尾截断和空贡献，不扩窗口或另挑方向/不确定性方法。
- **原全天parity是实现校验。** L95–101及130只在同次正式扫描核全天原den/qualified/distinct ID/有效grid精确匹配，格均值sum差≤1e-10、D差≤1e-12；容差已写spec，未看本轮结果后选择。原算术累计与新math.fsum可能有极小float差，固定容差合理；该输出不得作新增独立全天效果。
- **未知与资格可审。** 80%为全部窗内row的原qualified比例，cell≥100 distinct ID另列；不足时保留原数值/None和资格flags，不能由结果总体COMPLETE标签理解为信息优势已过。未保存的完整空grid原因不补造；`unique_grids_represented_in_coverage_rows`与`full_grid_total`明确分开，reference_UNKNOWN细因未保存则不伪造。
- **原件、单次与资源链。** L76–87/L109–114绑定旧输入身份、runtime、当前授权、source及release。L119–131同一次gzip读取同时压缩hash/字节数与EOF/CRC核对，未另扫原行情；L141–154排他formal marker先于检查，首正式失败/帽即停。Owner20CPU、review/root10、总30及128MiB/2MiB/单线程/12:16:20截止不变，不另开资源。

## 合成与准备原件

全文读synthetic.py、method-spec、synthetic-receipt及report-preparation；实读prepare完成/失败与两resource回执。12人工合成包括两端/最后完整秒、capture等号归格、原first在窗外不拿later替补、UNKNOWN/tie/nohint保分母、手算D=3验证订单→网格→方向权重、空cell、type7、19块恒定D=2及无有效复制不填0。不是本人重跑。

首prepare失败为人工fixture同一格混入不同stored reason，新guard拒绝；修fixture后第二次prepare PID62894/exit0，12项PASS。失败原件/资源保留，没有用真实同窗值调试。Owner两次记录CPU .058280+.073385，约 .131665秒（resource最后展示借记存在微秒级写入计时差），峰RSS24,772,608字节。metadata身份辅助计时CPU .001180秒，计本轮10秒review/root预留，非额外帽。

## 解释限制与后续验收

本轮只是固定人口/窗口断点定位：D描述原提示集合不利变动差，不是自身获单、净利润或准确率。即使两日D正且描述性区间支持，也只能让“提示到当前报价/成交/库存政策的转换”更值得解释，不能孤立alpha；若混合、跨0或资格不足应保留不确定，不强行二选一。

19块含很短末块，bootstrap为描述性、存在相关/非平稳及历史已见限制，不认证严格95%覆盖率或独立OOS。任何结果均不推翻已验完整现金的固定组合失败，不把D减费或与8格收益拼成独立样本。

待正式封存后只审两日全部摘要、4cell与块sum/count的已有标量一致性、分母/未知、有效复制和固定区间、parity/压缩读取/资源及版本，**不重跑聚合或bootstrap**。当前不预测结果或提前确认输入数值。本Reviewer只写本review，未改旧原件/Owner/Root/STOP、未联网/新增行情标签模型策略或交易，保护Library未访问。
