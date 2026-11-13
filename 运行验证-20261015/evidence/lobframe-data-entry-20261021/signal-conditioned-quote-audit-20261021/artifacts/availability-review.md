# signal-conditioned quoting / mm_queue：原件与许可有限审阅

固定commit：1644347871bb568a614ba9a6a9634c224dc6799b。唯一范围mm_queue，不审其他业务线。使用GitHub skill的gh只读API，未查认证/凭证；4个固定blob均核Git blob SHA匹配，URL/读取UTC见fixed-blob-receipts.json。收口UTC：2026-10-21 08:51:05。完整tree复用Root原件，truncated=false，没有重复获取HEAD/tree。文件发布/首次公开时间未独立核定，不把报告标题日期当发布时间。

1. **公开统计报告及派生行文件存在，但尚未形成可复核原始行情/成交包。** [研究README](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/docs/research/README.md#L117-L137)说recorder目录是唯一输入，并引用data/microstructure及stream_depth_<day>.csv。Root完整tree未列这些原始recorder/深度CSV；[.gitignore](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/.gitignore#L22-L29)默认忽略data/，公开导出JSON有例外。tree确列mm_queue_train.json与mm_queue_train.rows.jsonl（208,023字节），本Owner未载入其订单/收益数组。文件名及模拟fills汇总不证明真实逐笔订单、交易所成交或队列原件公开；原始文件当前是否另处公开UNKNOWN，不作全网不存在判断。

2. **作者已披露训练期深度限制，逐日原件manifest仍缺。** [mm_queue_train.md](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/docs/research/mm_queue_train.md)标训练22天（2026-07-30至09-03）、按queue_back/front模型评分择参。补读Root已保存的preregistration_mm_queue_2026-09-03.md后确认：作者明确披露训练期只有touch size，离touch一tick或更深的queue位置是模型盲区；09-03开始有depth sidecar，后续测试窗记录前五档及数量。因此不再将两个日期写成未解释矛盾。本Owner仍未取得逐日输入manifest/hash或原始队列数据，不能把模型填补当作全期观测到的真实深度。queue_front/back是队列成交模型，Fills/Total/CI不是账户或交易所成交回执。此修正仅复用本地预注册原件，没有新联网、数据读取或执行；具体补缺/回退逻辑仍由Root与代码Owner核验。

3. **MIT支持软件个人复用，行情与成交数据权利仍UNKNOWN。** [LICENSE](https://github.com/Pablozh123/prediction-market-terminal/blob/1644347871bb568a614ba9a6a9634c224dc6799b/LICENSE)为MIT、Copyright 2026 Pablozh123，要求保留版权/许可且无担保。没有取得原始recorder数据单独授权、供应商合同或对外数据再分发权；软件MIT不能自动覆盖这些外部权利。可作为纸面/源码研究材料，不足以认证个人可复现利润或真实队列成交能力。

本轮仅保存LICENSE、mm_queue_train.md、.gitignore及研究README文本与回执。未读取行情包、训练行JSONL、收益/预测/订单数组，未执行代码、模型、回测、账户或交易；不修改Root/其他Owner文件。
