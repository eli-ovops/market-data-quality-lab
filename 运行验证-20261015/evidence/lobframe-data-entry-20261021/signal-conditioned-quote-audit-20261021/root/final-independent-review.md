# 信号过滤报价：有限独立终审

审阅UTC：2026-10-21 08:53—08:57。实际model / effort：UNKNOWN；既有规则与原STOP沿用。**accept=true；must_fix=[]。** 接受整合报告为静态研究结论，不构成模型、回测或交易执行许可。

## 三项核验

1. **信号增量与后期对称报价的正模拟分开。** July文档的signal相对symmetric成交更少、总亏损减少，所列每fill capture / markout未见改善；整合报告不把总亏损下降当盈利，也不将少交易解释升级为已识别的因果机制。缺少等活动水平/风险对照已明示。October12更新研究的是对称queue规则，code Owner确认调用链默认symmetric；整合稿没有借此正数认证signal alpha。代码完整执行身份仍UNKNOWN，本终审复用代码Owner的静态证据，未重读/执行程序。

2. **损益与成交口径没有互相抹除。** quote_mid被传入mid_at_fill会改变capture / markout的经济归因，但不必破坏三价格项重构末端mark-to-mid的代数恒等式，整合稿保留了二者区别。October12表的0ms正、250ms负及去假设返佣后0ms仍正均以第三方模拟报告限定；没有将250ms称实测订单延迟，或把全部正值说成返佣造成。无统一本金、每天重置、末mid估值、29.746小时gap和本方live orders未验都披露，故不能读成5000美元真实账户结果，也未借其他机器人收益填充。

3. **日期及输入差异恰当限定。** 路径历史只返回一项commit；author / committer时间早于测试窗不等于不可回填、不可变的事前公开证据。整合稿对此保留UNKNOWN，没有将内部预注册自述升级为独立认证。预注册原文明确训练期touch-only，测试期增加五档depth，整合稿已承认这是披露过的盲区，不说成未解释矛盾。原始逐日文件/hash未取得和上游数据权利UNKNOWN仍是不同缺口。当前只停止升级个人盈利候选，不宣判所有预测模型无效、不扩大新策略分支。

## 实际阅读与分工边界

已全文阅读：

- `预测过滤-少交易与真实成交的边界-20261021.md`。
- `code/FINDINGS.md`、`artifacts/availability-review.md`。
- root四份研究md：`preregistration_mm_queue_2026-09-03.md`、`mm_status_2026-09-12.md`、`mm_pnl_july-2026.md`、`update_mm_queue_forward_2026-10-12.md`。
- `root/preregistration-path-history.json`：仅记录元数据意义，不以Git日期独立认证公开时间。

身份沿用固定commit `1644347871bb568a614ba9a6a9634c224dc6799b`；本轮没有重新核Git blob/hash、原源代码或外部原研究模块。表中数字是文档阅读，不读取派生JSON/JSONL行、行情、成交或收益数组，也未重算任何指标。

阅读时artifacts第2项尚以“具体缝隙”描述训练/深度差异，已向Root发送非阻断澄清建议：补明预注册已披露touch-only，剩余仅逐日输入身份未核。这不改变其“不能认22天都有真实深度”的正确限制，也不影响整合稿当前验收；本审阅不修改该Owner文件。

同轮整改复核：只补读artifacts修订第2项及整合稿首段。已明确训练touch-only/后期depth为作者已披露限制，不是未解释日期矛盾；整合稿亦明确signal是既有盘口不平衡阈值、非新学习模型，不恢复已关闭单一挂单压力实验。澄清闭合，`accept=true；must_fix=[]`维持；未扩大其余审阅范围。

无联网、模型、测试、前向、训练、回测、旧诊断重跑、账户或交易；仅新增本文件，不改回他人原件。通过的是报告边界与研究处分，不是个人利润或真实成交能力。
