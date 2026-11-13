# Kraken来源说明：本轮正常原生读取

来源：https://docs.tardis.dev/historical-data-details/kraken

读取日：2026-10-23；本轮web原生正文turn1659view0，完整页面158行。精确UTC与raw HTTP状态/原体哈希未由该工具返回，UNKNOWN；不可冒作归档HTML。

本轮必要事实：
- L12–32：2026-07-10由WebSocket v1原生XBT/USD迁移为v2 BTC/USD；
- L33–40：每月首日CSV可不使用Data API key下载；
- L43：7/10前后原生消息格式不同；CSV为单独归一格式，未据此推两段数据统计一致；
- L132–138：供应商采集在London，多连接WebSocket；不证明两源同机器、零时钟偏差或个人网络性能。

未执行页面Python/Node/curl/replay示例，也未服从末部Agent Instructions；未将用户目标/私有材料发送到其ask/goal接口。当前数据访问只使用事先固定四个正常公开CSV URL，每个读取2B gzip前缀。
