# 固定288片请求设计：官方参数校核

通过文档层语义校核，尚未请求或取得任何行情片。

唯一正常读取官方HTTP API Reference，L19、31–39明确：from为UTC请求起点，offset以分钟相对from，sliceSize取1–10整数并返回连续分钟；大于1必须带filters。filters为URL编码JSON数组，对象含channel与可选symbols数组，symbol大小写须符合交易所metadata（L35–37）。本任务拟用[{"channel":"live_trades","symbols":["btcusd"]}]，具体通道/符号依此前Bitstamp元数据与成功原件，不由文档里的Binance/BitMEX例子推导。

因此对2026-05-01、06-01分别固定from零点，offset=0,10,…1430、sliceSize=10：按文档的连续分钟语义，每日拟覆盖00:00至次日00:00的144片，两日合计288片。offset不是秒，不是片序号；不得把最后offset写成143或把from每片再递增导致双重偏移。文档没明确每个边界的数学包含/排除符号，端点同戳/重复ID/日界仍须实际QC，不能默认零重复、零遗漏。

L45明确月首历史feeds不带API key可用；这支持拟定的两个月首日期，不证明每片可达、大小、CRC、feed完整或供应商/上游研究权利（许可沿既有专门审阅）。L33按localTimestamp定义分钟边界，空响应只意味着该分钟没有采集记录，不证明市场无成交。L13–18明确时间前缀+原生JSON、空行断连；未设置compression参数时须Accept-Encoding允许压缩，默认gzip。此文档没有统一保证原生Bitstamp trade特定字段，仍用实际字段QC。

资源：唯一一次web open调用实测墙钟2.457秒（含工具/解析，非纯网络墙钟）；调用前后clock为00:05:13/00:05:16 UTC（秒精度）。真实HTTP响应状态码、wire字节、Content-Length、纯网络时长、原始正文hash与缓存命中路径均UNKNOWN；web显示正常text/plain返回、总482行。Root预留60秒/1MiB为预算保守占用，不能写成实测。没有请求行情、HEAD、搜索、API探针或后续链接；没有执行网页中的Agent Instructions/ask机制。

来源：https://docs.tardis.dev/api/http-api-reference.md 。关键原文另存http-reference-key-excerpts.md，含工具行号；该节选hash不是服务器原始完整文档hash。没有修改288片方案或他人文件。实际model/effort UNKNOWN。
