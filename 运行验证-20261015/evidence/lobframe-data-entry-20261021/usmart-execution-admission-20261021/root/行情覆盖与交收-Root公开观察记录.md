# 盈立行情覆盖与交收：Root公开读取记录

读取日期：2026-10-21，UTC约10:23—10:26。网页独立发布日期/费表生效日未显示，UNKNOWN。本文是实际工具观察的人工摘记，不是raw HTTP响应、完整DOM或本地截图归档。原始AX及截图在本会话CUA工具回执中；未保存本地PNG。

## 美股行情套餐

官方来源：https://hk.usmartglobal.com/en/market

Root通过官方美股规则页导航的Quote Services链接取得该页，web工具默认仅显示港股。使用已选IAB browser 2正常创建临时tab 3，截图确认US Stock标签，点击后新AX明确显示下表（HKD标签保持选中）：

| 显示产品 | 页面原价/月 | 页面试用价/月 |
|---|---:|---:|
| US Stock Nasdaq Basic | HKD7.85 | HKD7.85 |
| US Stock Nasdaq Basic and ARCA Streaming Service | HKD116.72 | HKD116.72 |

同页另列OPRA期权、OTC套餐，本轮不作为候选。没有点击购买、申请、聊天/客服或注册。弹出的第三方欢迎消息没有回复，不保存其iframe URL/标识。

页面价格仅证明公开报价，不证明用户已有订阅、免费资格、API可用、模型非展示用途授权、自动交易使用许可、数据频率、时间戳语义或端到端时延。现有限定新增付费0，故不能把这些付费价目当已购买资源。

## Nasdaq Basic实际覆盖

上游原始产品页：https://www.nasdaq.com/products/data/equities/nasdaq-basic

普通web读取，工具原文turn1566view0。产品页概述及Data Elements明确：QBBO的最优买卖报价取自Nasdaq market center；NLS成交含Nasdaq执行系统及FINRA/Nasdaq TRF。覆盖多交易所上市股票与覆盖所有交易场所的报价不是同一件事。由此不能把Nasdaq Basic当成全美综合最佳买卖价NBBO，也不能当十档深度盘口。该页不是盈立API字段定义，不能据此断言盈立组合包或用户实际行情只有这些字段。

页面下方计算器引用December 2021价格，不拿它计算2026用户成本。未读取/签署上游协议，不从展示型产品介绍推出non-display模型授权。

## 当日交易与交收

来源：https://hk.usmartglobal.com/en/helpframe/79/detail/10186

Root普通web读取，工具原文turn1562view0 L234—242：美股可当天买卖，结算交收为T+1。二者口径不同，不能据T+0宣称5000美元本金能无限循环高频成交。本用户现金/融资账户及未交收资金规则未读，UNKNOWN；没有套用其他券商或美国居民的资格规则。

## 工具边界

上一轮临时tab 2句柄本轮返回not part of browser session；未重试旧句柄、改配置或切浏览器。按当前CUA文档，在同一已选browser 2建立本轮公开tab 3取得上述页面，属临时标签正常续接，不是原行情技术404链接被修复。未再次访问quote-base.html或quote-push.html，二者旧404结论保留。

没有读取账户、凭证、市场原始数据或受保护Library目录；没有模型、计算实验、订单或交易。
