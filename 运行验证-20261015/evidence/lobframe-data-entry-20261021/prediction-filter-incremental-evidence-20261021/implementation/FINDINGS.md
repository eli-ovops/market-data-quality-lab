# 预测过滤相对随机少报的公开实现证据

**本轮没有取得足以支持该增量的对照证据。** 唯一深入对象为开发者原始仓库[punyamodi/Deep-Market-Maker](https://github.com/punyamodi/Deep-Market-Maker)，不是第三方复刻。公开动作6/6，读取UTC窗口2026-10-21 12:35:54—12:37:04。实际model/effort UNKNOWN；规则沿派单。纯文本静态研究，无源码执行、数据包/收益数组读取、模型或交易。

1. **确有预测影响报价的实现入口，但不等于随机过滤对照。** 直接读[src/simulation/backtest.py](https://raw.githubusercontent.com/punyamodi/Deep-Market-Maker/master/src/simulation/backtest.py)全109行：L97—108的`compare_strategies`对同一events分别调用`use_toxicity=False/True`；L70—80接入toxicity model、阈值、spread multiplier和size scale。默认毒性高阈值0.65、价差倍率2.5、规模倍率0.5（L23—35）。故不是单独改变是否报价的干净实验；报价宽度、规模、成交/库存风险也可变化。已读比较函数没有随机少报、等报价时长、等报单/撤单/成交量的校准或对照臂，不能据此隔离预测选时价值。未核全仓，不能声称仓库其他位置绝无此对照。

2. **属于模拟入口，不是已验实盘成交/费用账。** L82—95构造概率队列fill model及latency sampler；返回声明包含fills/PnL序列/汇总，但本轮没有读取这些数组或实际输出。README只描述simulated exchange、队列概率、延迟和费用模块；真实订单/取消/成交ID、逐笔费用/返佣原件链未取得，费用具体参数和取消/随机种子共用机制UNKNOWN。相同events不保证两臂使用同一随机成交实现。本轮也没有验证模拟成交规则或实际运行可复现性。

3. **当前材料仅支持“有可检查的框架”，不支持增量结论。** README示例将`toxicity_model=None`，而代码L56—58定义None为纯A-S；因此该示例和漂亮图不能证明启用预测后的收益，更不能证明超过等活动量随机少报。固定提交取得失败，实际只核master当时返回源码；完整commit、发布时间、完整tree和许可UNKNOWN，不把当前分支当不可变原件。若要判断本问题，尚缺同期、相同活动量/执行约束的随机或置乱预测对照及其可核订单/成交/费用输出；这是证据缺口，不是本轮运行建议或执行授权。

范围与阻断：两次发现query后只选上述仓库；匿名commit metadata请求SSL EOF，查LOCAL_BLOCKERS后原生同URL仅not accessible（源HTTP UNKNOWN），未改TLS/身份/代理。正常仓库网页与公开raw源码可读；不是403后的绕取。6项预算已止，无其他候选深入或补跑。排除清单旧案均未重开。采用[GitHub skill](/Users/USER/.agents/skills/github/SKILL.md)的路径核验方式；因本轮禁用账号密钥，仅匿名公开读取，无认证动作。
