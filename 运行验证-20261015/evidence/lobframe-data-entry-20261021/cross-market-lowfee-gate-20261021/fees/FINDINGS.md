# Lighter 零费准入核查

日期：2026-10-21；UTC 读取窗口 09:31:29—09:32:12。仅公开文本研究，无钱包、账户、交易 API、行情或模型操作。实际 model/effort：UNKNOWN。规则：PERMISSIONS-2026-10-14-v1、ROUTING-2026-10-13-v4、HANDOFF-2026-10-10-v2。唯一写入本 fees 目录。

1. **零基础交易费表项已证实，但不是所有账户/订单都零费。** 官方 [Account Types](https://apidocs.lighter.xyz/docs/account-types) 明列默认 Standard maker/taker 各 0%；Standard 的 TWAP 收 1bp。Plus 各 0.005%（0.5bp）；Premium 零质押时 maker 0.0040%（0.4bp）、taker 0.0280%（2.8bp）。Premium 的 LIT 质押优惠最高档为 500,000 LIT、减费 30%；fee credits 也计入相应质押参数。该页未列 Standard 的成交额、质押或付费会员门槛；这不等于已核全套资格条件。页面仅显示“Updated 3 days ago”，精确发布日期/生效日 UNKNOWN，不能据此回溯全年历史费率。

2. **成交额要求影响 Plus/Premium 的交易请求额度，不能混同于 Standard 零费条件。** 官方 [Volume Quota](https://apidocs.lighter.xyz/docs/volume-quota-program) 说明其仅对 Plus/Premium 实施：每 2 USD 成交额增加 1 额度，新账户 1,000，最高累计 15,000,000，额度不失效；每 15 秒有一次不耗额度的 SendTx，子账户共享。它是请求额度制度，不是成交获利证据；本核查不建议为额度制造成交。文档“Updated 2 days ago”，精确生效日 UNKNOWN。零费也不消除价差、冲击、跨市场另一腿或运营成本；这些成本本轮没有量化。

3. **个人零费准入整体尚未通过；地区资格和费用适用范围仍 UNKNOWN。** Account Types 首句明确 API 用户可使用 Standard/Plus/Premium，故该页不是只针对手动界面的费用表；已读页没有禁止 Standard API 或自动策略的条款。但本页不是完整服务条款，不能由此确认自动策略的一切使用许可。`docs.lighter.xyz` 费用与地区路径均未取得正文，HTTP 原状态 UNKNOWN；未重试或换身份/通道。未取得官方中国内地常住用户限制条款，不能把公开 API 费用表当作准入许可，也不能据缺条款声称全球不可用。已读费用表未明确分别覆盖 perps/spot（且明示 binary options 另表），故不能推广为所有产品零费；名义额计费基数、开仓/平仓逐次适用、资金费、清算、入出金/链上及第三方附加费的准确现行规则均 UNKNOWN。现有证据只通过“Standard 存在 0% maker/taker 官方表项”这一层，不能放行具体个人账户使用，也不能证明短期跨市场预测具有净利润。

## 实际覆盖

7 个搜索查询/页面对象：3 条搜索查询（初始查询一条、定向官方查询两条）、4 个页面（2 成功、2 工具不可访问）。未读取第三方正文；第三方摘要仅作为未采信线索。当前两成功页为 API 文档，不等同于完整平台条款。时延由其他 Owner 核查，本报告不推断本机实测时延。
