# 官方HTTP参考：必要参数原文

URL: https://docs.tardis.dev/api/http-api-reference.md
实际读取UTC区间：2026-10-22 00:05:13–00:05:16。文档发布/修订日期UNKNOWN。
以下为唯一一次web open正常返回的关键片段（保留工具行号；不是整页原始HTTP正文）：

L31: requested UTC start date of historical market data feed

L32: Minute offset that, together with `from`, specifies the first minute of historical data returned.

L33: Minute boundaries are based on `localTimestamp` (when we received the message), not exchange event timestamps. An empty response for a given offset is normal and means no data was recorded during that minute.

L35: URL-encoded JSON string in `{channel:string, symbols?: string[]}[]` format

L38–39: Number of consecutive minutes returned by one request. Valid values are whole integers from `1` to `10`. Default is `1`. Values greater than `1` require the `filters` query parameter.

L45: Without API key historical data feeds for the first day of each month are available.

上述英文原文合计少于200词；没有复制行情示例或文档内Agent Instructions。
