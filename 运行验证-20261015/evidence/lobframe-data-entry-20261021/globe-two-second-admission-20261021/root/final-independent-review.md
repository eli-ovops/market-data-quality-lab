# Globe案例有限独立终审

审阅UTC：2026-10-21 08:36—08:39。目标既有Sol / medium；实际model / effort：UNKNOWN。沿用 PERMISSIONS-2026-10-14-v1 / ROUTING-2026-10-13-v4 / HANDOFF-2026-10-10-v2。

**accept=true；must_fix=[]。** 接受现稿作为有边界的纸面/源码研究结论，当前停在模型/策略运行准入前；不构成新执行许可，也不宣判所有TCN、盘口预测或作者未公开运行失败。

## 三项核验

1. **71%与多数类基准采用同一主表，76%保持独立。** 实际查看既有root/page4.png：Figure2(d) support为Down61142、Stable350499、Up53759、总465400；Avg recall .71、Accuracy71%。Root用该同表计数列出的Stable基准75.311345%和约4.31个百分点差，有明确分母。这里只核标量拆分口径，不重跑预测。Down .61和Up .66在该表为recall，不是预测方向的precision或下单胜率。实际查看root/page9.png：Appendix B另表约76%，没有support，因此现稿不把其与465400个样本直接比较，不择优合并。未胜多数类总体accuracy不等于没有少数类信息，现稿保留这一点。

2. **源码问题没有被反推成作者全部运行的定论。** Root明确将test用于val_loss控制后再预测同test的事实限定到已读WalkForwardV2 / Walkthrough静态链，不将未走梯度误当未参与选择，也不宣称这些notebook已被证明产生论文各表。归一化后比例标签、标签中心对齐和方向名差异均保留为复现链问题；未把前一日统计误称当日未来泄漏。此项复用model Owner全文审阅的分工证据，本终审没有再次读取全部notebook或执行源码，不能冒称独立确认实际运行状态。

3. **许可、预测指标与赚钱结果没有越界。** MIT明确只支持其覆盖的软件复用，不自动覆盖精确Dropbox行情归档；链接存在与当前可达、身份/hash及行情权利未核分别保留。预测目标是平滑mid分类，不是可成交报价或完整个人净利。现稿没有从准确率补造费用、成交、收益或容量；保留研究样本但不按现有notebook追加训练，旧A能力失败和STOP不改变。缺少运行身份、独立评估或全成本证据是当前准入不足，不是已经证明全模型无效。

## 实际阅读与限制

- `两秒预测-准确率与赚钱证据-20261021.md`全文。
- `model/FINDINGS.md`全文。
- `artifacts/availability-and-license.md`全文。
- `root/pdf-source-receipt.json`原件；记录公开PDF身份SHA256 `3d25a7ca56811156cef12680574c39ffa60533bbbc97b1a9de422b46894f4a9f`。本终审未重新读取PDF二进制/独立验hash。
- `root/page4.png`、`root/page9.png`实际视觉读取。最初误用不存在的pdf-review子目录，读取失败后查LOCAL_BLOCKERS及限定root文件清单，随后只读已有正确路径；未重渲染、联网或重下载。

本轮无模型、训练、前向、回测、行情/权重/收益数组读取、旧诊断重跑、外联、账户或交易；不改其他原件。仅本审阅文件新增写入。通过的是报告口径和当前停止准入的结论，不是策略盈利或可运行验收。
