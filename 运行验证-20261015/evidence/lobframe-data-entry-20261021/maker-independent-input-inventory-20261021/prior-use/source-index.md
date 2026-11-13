# 本轮12份来源：file+line

以下行号为原文本一基行号。只读这些方案/JSON元数据/MD的指定段；引用某文件不表示本轮打开其下游行情或源码。

1. **S1**：[十档盘口原方案](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021/十档盘口-一次历史留出验证方案-20261021.md:17>)：L1–45；日期L17–25、训练统计L39。
2. **S2**：[九文件data-receipt](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021/execution-20261021/data-receipt.json:208>)：定向读日期/split/QC/scope字段；九日区段L12–450，May L208–254、Jun L257–303，data阶段scope L453–458。没有打开其path所指缓存。
3. **S3**：[fit-A](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021/execution-20261021/fit-A.json:9>)：全文L1–24；验证日期/误差/计数L9–23。
4. **S4**：[原终态回执](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021/execution-20261021/terminal-receipt.json:17>)：L1–65；STOP L9–10，实际fit/epochs/样本/测试/经济账L17–29。
5. **S5**：[训练输入封存](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021/execution-20261021/training-input-seal.json:5>)：全文L1–45；Jan—Mar计数L5–38、输入/目标/统计hash L40–43。不读hash所指数组/统计内容。
6. **S6**：[E/S诊断人类报告](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021/diagnosis-forward-once-20261021/owner/FINDINGS.md:15>)：L1–32；只TRAIN及无更新L15–20，无VALID/TEST/校准/费用L28。
7. **S7**：[后续跨市场方案](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021/cross-market-independent-plan-20261021/跨市场信息-一次独立挑战最小方案-20261021.md:15>)：L11–25；拟训练/验证/未来日期L15–21。方案不是完成回执。
8. **S8**：[后续Stage0人类报告](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021/cross-market-independent-plan-20261021/execution-20261021/owner/report.md:43>)：L43–61；三日经济必要空间观察L49–55、后段未执行及May/Jun未读本阶段L59。
9. **S9**：[此前prior-use报告](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021/cross-market-independent-plan-20261021/prior-use/FINDINGS.md:21>)：全文L1–39；Oct1成本范围L21–27；历史独立性限制L29–37。它早于后续Stage0，本轮不把其“尚未发现Jul—Sep费用观察”延续为当前事实。
10. **S10**：[旧Kraken 60秒提案](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/BTCUSD-fixed-forecast-protocol-20261017/protocol/proposal.json:15>)：全文L1–93；身份/未执行L2–8、候选日期L15–27、执行零L91。只读提案文字，没有取任何Kraken输入。
11. **S11**：[旧提案closure](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/paper-reuse-20261015/BTC60s-fixed-forecast-protocol-not-executed-phase122-closure-20261017.json:39>)：全文L1–42；models/backtests/trades零L39–41。
12. **S12**：[2026日频/年度选择链用途审计](</Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/annual-2026-holdout-challenge-plan-20261019/selection/selection-chain-audit.md:3>)：全文L1–53；核心已处理/未纳固定拟合与评分/选规UNKNOWN L3、9–16；选择消息缺口L20–27；以往读取暴露披露L29–37。未打开其F01–F08、会话索引或行情。
