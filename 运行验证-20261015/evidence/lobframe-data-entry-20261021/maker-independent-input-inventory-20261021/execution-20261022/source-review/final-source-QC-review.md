# 最终独立来源/QC验收

**PASS_WITH_LIMITS；本范围未发现must_fix。** 全固定请求账/封存链已核，另抽查6/288个原始压缩片。不是重跑全数据QC或方法/收益验收；候选通过不等于个人净利。

## 288个固定请求与采集记录

独立读取GET-ledger.jsonl与raw-QC-ledger.jsonl全部小型元数据，共288条GET、288条QC。逐条解码URL：仅https://api.tardis.dev/v1/data-feeds/bitstamp；from分别固定2026-05-01/06-01零点；offset每日0,10,…1430齐；sliceSize=10；filters严格为live_trades/btcusd。288个唯一URL、attempt序列1至288，无重复URL/重试、认证或重定向记录，全部HTTP200/body_complete/gzip；总正文2,838,806B。相邻请求完成后启动间隔最小1.005294秒。

每日日seal均144片，与总data-seal.days逐字段一致；slice_counts与对应144条raw-QC账逐字段一致。GET/QC账实际文件SHA匹配data-seal绑定。按Owner全片QC账：288份gzip EOF/CRC通过，identity响应0、空片0；trade报告共74,722条，May29,634、Jun45,088，另5条订阅确认和5个空行断连标记。trade记录数不是独立主动订单数。

记录覆盖边界：May首接收00:00:00.1048505，末23:59:34.5001335；Jun首00:00:00.0982039，末23:59:56.6669974 UTC（包括非trade消息，依据QC账）。连续固定切片返回不意味着全天每个时点有消息，更不等于交易所完整feed。May封存1段闭合断连区间，Jun4段，其中各有日尾缺后锚区间；没有隐去这些缺口。普通静默不被本审阅判作额外断连。

## 事先固定的原件见证：每日offset0/720/1430

在读片前固定起/中/末三片，不按结果挑片。以下6片实际压缩SHA均匹配GET账；分别完整解压读至EOF验证这6片gzip CRC，只对每片前最多3条非空消息解析字段/时钟，其余字节仅排空CRC。没有价格指标、标签或收益运算，未核其他282片原件的实际压缩SHA/CRC。

| 日期/offset | 压缩字节 | 实际压缩SHA256 |
|---|---:|---|
| May1/0 | 7096 | 83f43028c7c0483f7759635cfb8039645ebeb5733e1882c8d923427e6df7383b |
| May1/720 | 5861 | 23d08c5a90e5b38b5df9f61c149e8ffa9ded10d6f25e054ea87ef47f937bdbe2 |
| May1/1430 | 3316 | 1626aafdf3fd16af9a2615b586128d375a8cf9a74088bbceb9591045688f5ca2 |
| Jun1/0 | 12511 | 9d66d3499953cad1791c6989727ebae609ac42a20cd0f21cdb47a59f7a50e231 |
| Jun1/720 | 30801 | 7f15c82378cd7ee204ba0e1ff3470d66027dc46b5d3e33b8bc3af7ee3bfa7991 |
| Jun1/1430 | 8102 | 800f70fae67e816c353a582b5cf1580b48bdf471727421b2c743bb1b469fb275 |

18条消息见证全部channel为live_trades_btcusd、七位小数UTC接收钟；两日首片首消息各为订阅确认，其余所见trade均包含amount/amount_str、buy_order_id、sell_order_id、id、microtimestamp、price/price_str、timestamp、type，源microtimestamp为十进制文本，type为0/1。字段存在性/类型抽查不冒充全片价量合法性和完整时序重算；后者依已审源码与Owner全量QC完成账。

## 源码/输入/摘要及运行身份

正式first-started UTC00:19:32.729767、PID59667，来源hash与新preparation-seal完全一致，当前core/analysis/run/tests/parameters实际小文件hash亦匹配；Root formal-release绑定seal SHA f2a724017607c944f32da7cbf0ddbef0503d65fa9ae5300704fd6550cbe34a99。启动receipt固定项目.venv/bin/python、3.12.14，符合已验runtime修订。未发现第二次正式启动或终态重跑证据；这限所查目录与账，不宣称操作系统全局取证。

May/Jun normalized压缩文件仅重算SHA，与各日data-seal分别fe6b9104265703257dd823319d422b29b474156a45cdd7f9a4e65b2e717b63f3、9702bccd2346914f65aca0c0724334076e4076f51bdb4ad0c7425dd6f71f845b匹配；两份coverage压缩文件仅重算SHA，均与summary绑定匹配。没有解码/加载normalized或coverage的价格/标签数组。旧大BBO未重扫，沿原preflight与已核May/JunSHA/CRC身份。

摘要覆盖账：May固定分母29,616、合格未来参考标签29,615；另18条分母域外；Jun分母45,085、合格45,040，另3条域外。差额分别1条下一报价时钟不确定、34条年龄超1秒及11条BBO无效/冲突/源钟倒退（Jun）。这些是Owner摘要原值，未由Reviewer重算标签；源钟未来guard等原因另列，不把它们混作已从固定分母删除。raw trade数分别等于固定分母+域外数。四cell独立被动ID计数May1549/1853/1442/1281，Jun3485/3746/3120/3178，属于结果元数据，不是实际个人订单。

正式resource终态UTC00:28:16.140040：288GET、2,838,806B、网络222.405636s、计算wall12.865506s、CPU16.923449s、峰RSS156,827,648B、Owner目录当时11,409,573B、单线程；连同既有保守预留，计算207.702452s、网络282.405636s、下载3,887,382B，低于所定帽。待写manifest/report会稍增磁盘，不把资源回执时点冒称最终全部文件大小。正式stdout含同一终态与data_sealed，stderr0B；Root已工具观察exit0（本轮未重查进程或伪造退出码）。读取时Owner独立completion/terminal/最终manifest尚未出现，本审阅不把尚未保存文件称已验收。

## 结论边界

证据支持：固定两日、公开无认证供应商历史请求实际完成，采集记录/字段与封存链可用，已描述缺口；不能据此证明上游每笔成交全覆盖、采集钟绝对误差、用户本机实时可及性、订单排队/自身可成交或交易准入。result标HISTORICAL_MECHANISM_CANDIDATE_ONLY而费用辅助标NO_POSITIVE_QUALIFIED_SPACE_FIXED_1S_EXIT，二者不应互相替代；本审阅不把统计候选结论改成净利。

仅保存本审阅，未改原件、Owner/Root源码或STOP，无网络/账户/模型/分析重跑。最后一轮小文件身份核验CPU0.008402s、wall0.021791s；前述元数据/6片抽查命令未单独累计CPU，不能将该末轮计时冒充全审阅总耗时。全审阅在Root共享180s计算预留内仅做少量标准库读取，最终预算由Root合并；实际model/effort UNKNOWN。

保存UTC：2026-10-22T00:31:23.963241+00:00

## 末端证据补读

Owner随后已保存formal-completion-receipt.json（UTC00:30:08.945457）：同一session32302/PID59667，formal_exit_code=0、formal_attempts=1、GET_attempts=288、raw正文2,838,806B、stderr0，first_stop不存在。其result_sha256和preparation_seal_sha256由本Reviewer对小原件独立hash核对匹配。故先前“尚未见completion”仅为初次读取时点状态，现末端退出回执已核；不再扩大原始片抽查。PASS_WITH_LIMITS保持。

特别保留：原始账中的5个断连标记及BBO snapshot实际/上游未知覆盖，不能被约99%以上的“在已收到trade分母内可配未来参考”标签覆盖率抹掉。高标签覆盖不衡量缺失成交、采集前未收到消息或盘口两次更新之间的完整状态，也不证明个人实时获知及行动性。

补读UTC：2026-10-22T00:31:39.232105+00:00
