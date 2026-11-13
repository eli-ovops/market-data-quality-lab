# 最小官方原文及费用事实摘录

UTC 读取窗口：2026-10-21 09:31:29—09:32:12；逐请求秒级 UTC UNKNOWN。仅摘录已取得原页，未追加网络读取。

来源：https://apidocs.lighter.xyz/docs/account-types

原文 L19：
> Lighter API users can operate under a Standard, Plus or Premium/Advanced account.

原文 L56：
> For standard accounts only, TWAP orders charge a 1bps fee.

以下为原表数值事实（非新增账户实测）：

| 账户/质押量 | maker | taker |
| --- | --- | --- |
| Standard/default | 0% | 0% |
| Plus/opt-in | 0.005% | 0.005% |
| Premium/0 LIT | 0.0040% | 0.0280% |
| Premium/1,000 LIT | 0.0039% | 0.0273% |
| Premium/3,000 LIT | 0.0038% | 0.0266% |
| Premium/10,000 LIT | 0.0036% | 0.0252% |
| Premium/30,000 LIT | 0.0034% | 0.0238% |
| Premium/100,000 LIT | 0.0032% | 0.0224% |
| Premium/300,000 LIT | 0.0030% | 0.0210% |
| Premium/500,000 LIT | 0.0028% | 0.0196% |

API 用户可用 Standard 由首句直接支持；自动策略许可的完整合同边界未核，不把未见禁止当作全部许可。

来源：https://apidocs.lighter.xyz/docs/volume-quota-program

原文 L29：
> New accounts start at 1K quota, and you can stack at most 15.000.000 TX allowance in your volume quota, which does not expire.

该额度仅对 Plus/Premium 生效的适用范围按本目录 FINDINGS.md 中的事实转述；不是 Standard 零费所需成交额。
