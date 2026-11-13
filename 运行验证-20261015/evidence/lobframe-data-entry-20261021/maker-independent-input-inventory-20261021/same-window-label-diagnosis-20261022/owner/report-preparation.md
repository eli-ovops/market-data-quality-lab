# 精确同窗标签聚合：准备回执

PREPARED_NO_SAME_WINDOW_RESULT：未读取coverage正文，未产生新同窗D/区间。只核旧manifest、小summary/参数/analysis文本身份和coverage stat，未导入旧analysis/core、运行grid_states/标签/firstID或任何策略。

固定grid5..32449含两端，最后一格原观察到09:00:50；只重用原selected_first、合格标签及原z/hash侧，所有未入样/未知仍在窗口coverage行分母。原四cell先网格内订单等权，再每方向/政策有效网格等权，方向各半；ID计数不重选。状态/原因按已存字段逐行及已见grid统计，coverage没有保存完整空grid状态则不推造；reference_UNKNOWN详细原因未存不补查行情。

预审不确定性已固定为19个UTC30分钟截断单元/日（0..18，含首尾短块/空贡献），单Random(20261021)，1999rep每rep先May19后June19，联合四cell sum/count，不平均块D；每日日四cell均有count才有效，各自至少1900才能type7区间。辅助两日等权仅同rep双日有效、也需1900。短窗口/短尾块及历史已见限制保留，不把区间作独立OOS或盈利证据。

同一次正式扫描将同时验证旧全天已有den/qualified/ID/grid计数精确相等、grid sums误差<=1e-10bp、D误差<=1e-12bp；仅实现引用一致性，不声称新的独立全天效果。正式单次读取内同步计算压缩SHA、gzipEOF/CRC及行聚合，不另扫行情或重算label。失败/触帽首停不结果后修复重跑。

12项合成通过：两端grid/完整最后秒、capture-grid兼容、旧first在窗外不以laterID替补、未知/tie/无提示/零分保分母、手算订单→网格→方向D=3、空cell DUNKNOWN、首尾块保留、恒定D=2配对bootstrap、无有效复制不记0。首轮人工fixture将同一grid混配zero/nonzero原因，被一致性guard拒；已修fixture到另一grid，旧fixture/失败回执资源保留。未动真实数据或用新结果调试。

实际项目Python3.12.14；12PASS回执、资源、helper/spec/preparation-seal齐。seal a9fb072a9b6c646f1463c5a0f9f0280449ad1db8c435bc445bb88e965a5c64a0。Root release合同status=RELEASED_ONE_CACHED_LABEL_AGGREGATION并绑定本seal；独审和Root放行前不formal。Owner20CPU+审阅Root10、128MiB/2MiB/单线程、12:16:20UTC截止，网络/数据/安装/付费/账户交易0。actual model/effort/speed UNKNOWN，原规则版本不变。
