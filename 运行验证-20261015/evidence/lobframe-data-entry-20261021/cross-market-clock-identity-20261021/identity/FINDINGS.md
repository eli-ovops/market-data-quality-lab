# Kraken 同期现货数据身份核查

日期2026-10-21。实际model/effort UNKNOWN；沿PERMISSIONS-2026-10-14-v1、ROUTING-2026-10-13-v4、HANDOFF-2026-10-10-v2。本轮仅一次公开覆盖元数据GET，无行情请求、HEAD、认证、模型或回测。仅写本identity目录。

1. **两段原生符号与CSV符号可在官方覆盖目录对应，不能全年固定写BTC-USD。** [官方exchange metadata](https://api.tardis.dev/v1/exchanges/kraken) 的 `availableSymbols` 与 `datasets.symbols` 给出以下精确记录，均为 `type=spot`。另复用已保存的[官方Kraken说明](https://docs.tardis.dev/historical-data-details/kraken)的v1→v2变更与BTC/USD例子；本轮未重复取该说明。

| 区间边界（原字段UTC） | 原生id | CSV datasets id |
| --- | --- | --- |
| availableSince=2019-06-04T00:00:00.000Z；availableTo=2026-07-10T00:00:00.000Z | XBT/USD | XBT-USD |
| availableSince=2026-07-10T00:00:00.000Z；CSV availableTo=2026-10-21T00:00:00.000Z（本轮读取时） | BTC/USD | BTC-USD |

原生BTC/USD记录没有availableTo；CSV记录有上述截止。不是把XBT/USD字符串直接用作CSV文件名，也没有把USD与USDT/USDC混同。

2. **两段CSV目录均列出所需三种数据类型，九个月首日存在覆盖范围交集。** 两条CSV记录的 `dataTypes` 都包含 `book_snapshot_25`、`quotes`、`trades`，另有 `incremental_book_L2`、`book_snapshot_5`、`book_ticker`。因此本任务日期身份如下；同一日期的Bitstamp身份来自既有 `execution-20261021/data-receipt.json`，本轮仅解析其日期/URL/状态字段。

| 2026同期日期 | Kraken CSV symbol | 已有Bitstamp CSV symbol |
| --- | --- | --- |
| 01-01、02-01、03-01、04-01、05-01、06-01、07-01 | XBT-USD | BTCUSD |
| 08-01、09-01 | BTC-USD | BTCUSD |

Kraken样本文件身份候选模板为 `https://datasets.tardis.dev/v1/kraken/{dataType}/2026/{MM}/01/{symbol}.csv.gz`；这里只列身份，不访问模板URL。已保存Kraken说明称月首CSV免API key，但这不证明每个具体文件已取得。

3. **仅通过元数据身份层，文件与同步层仍UNKNOWN。** 官方覆盖JSON的 `datasets.exportedFrom/Until` 为2019-06-04与2026-10-21的00:00:00.000Z。此次HTTP200、完整JSON解析及SHA仅属于覆盖metadata：不能当作Kraken九天CSV的可达性、Content-Length、文件SHA、完整性或逐日无缺口证明。Kraken固定文件实际取得、行数、格式QC、两市场共同现实可知时钟及因果同步均UNKNOWN；原生v1/v2及spread/ticker变化也不因CSV类型名称相同而消失。既有Bitstamp九文件QC通过不替代Kraken文件QC或配对同步证据。

## 原件与读取回执

- `kraken-exchange-metadata.json`：官方原始覆盖JSON，689,207B；SHA256 `fbfd4482ee4708318a42014e247e5e91cf7927bd5012c703825ee64170c8e07c`。HTTP200，Content-Type application/json，Date Wed, 21 Oct 2026 09:52:49 GMT。该响应未提供独立文档修订日期，UNKNOWN。
- `metadata-source-receipt.json`：准确UTC开始2026-10-21T09:52:49.038546+00:00，结束09:52:49.655296+00:00；响应头、正文应用字节、2MiB硬帽与hash。一次普通无凭证GET，未重试。
- `target-symbol-extract.json`：从上述已保存metadata离线选出的两条原生记录和两条CSV记录，非额外API请求。
- 复用本地 `../../cross-market-paired-data-admission-20261021/root/kraken.native.txt`；没有假称本Owner独立重读该网页。该说明未显示出版日期；不推测日期。
- 小读 `../../execution-20261021/data-receipt.json` 九个日期及文件身份状态；未读取任何压缩CSV或行情数组、未访问受保护Library目录。

公开对象预算使用1/4；信息已足够回答本层，不为耗尽预算追加请求。
