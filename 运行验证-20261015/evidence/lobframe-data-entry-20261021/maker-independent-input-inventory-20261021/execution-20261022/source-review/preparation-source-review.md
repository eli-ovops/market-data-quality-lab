# 正式获取前：来源与数据QC静态审阅

状态：**MUST_FIX_RUNTIME_RECORD / 其余来源与数据项PASS_WITH_LIMITS**。未运行任何Owner源码、模型、预检、市场请求或行情读取；不代替方法Reviewer。

## 唯一must_fix：正式解释器与封存记录不一致

`owner/preflight.json.Python`为3.12.14；`owner/preparation-seal.json.runtime_Python`却为3.9.6。`owner/core.py:172`使用`@dataclass(slots=True)`，需要Python≥3.10；若照最终seal标记的3.9执行会在导入阶段失败。请正式启动前固定解释器绝对路径及版本，并让当前来源seal与实际正式命令一致。不需为回执身份修正重复扫描May/Jun行情；当前core/run/parameters相对预检未变。该项已即时发Root。本审阅未擅改他人文件或发起运行。

## 已核通过的具体来源/QC路径

- 固定请求：core.py:17、131–132、210–218固定May1/Jun1，每日range(0,1440,10)，from为各日00:00:00.000Z、sliceSize10，过滤URL编码JSON数组live_trades/btcusd；串行、请求后至少等待1秒。静态上是两日288个不同切片地址，未将它们当实际已得片段。与本目录已保存官方参考L19/31–39及45一致：offset分钟，按localTimestamp切片，有filters可10分钟，月首免key。没有把CSV符号BTCUSD误送为原生API symbol。
- 拒绝/获取：core.py:128–169禁重定向、不带认证、仅GET、Accept-Encoding gzip。非200/异常立即向外抛出，无重试/换源/换日期分支；run.py:57–65封first-stop。Content-Length若超剩余字节帽不读正文；接收按剩余额度分块，保留实际字节与SHA。x-name存在时核对应切片；它缺失时不伪称响应头身份已核。
- 压缩/identity：Content-Encoding仅接受gzip或identity（缺省视identity），gzip.open完整迭代至EOF以触发CRC校验；identity靠完整HTTP体及字段/时间域验证，不伪造gzip CRC。原件均保留，SHA及HTTP头进入GET-ledger；normalized日文件、GET/QC账哈希封入data-seal（core.py:220–222）。CRC/完整HTTP体不等于交易所feed完整。
- 原生字段：core.py:87–95、177–207强制七位小数UTC接收文本，用整数100ns保存，不浮点截断；源microtimestamp为十进制整数字符串，保留整数µs。type仅整数0/1，id和双订单ID必须是整数/十进制字符串；price_str/amount_str优先并用Decimal核有限正值。重复tradeID跨同日各片即停，接收倒退/片外消息/错channel即停。数量只QC且原始保留，不在normalized记录中供分析使用，符合本次数笔数而非数量规则。trade.type含义沿已核原件映射，不混order_type。
- 订阅/空片/断连：非trade单独event计数，白行作为明确断连；前最后/后第一接收钟闭合gap，首尾缺锚用日界（core.py:183–190、219）。空片/无trade保留描述，不自行当断连；符合冻结提案现第22行，不把普通静默另设事后gap阈值。analysis.py:67/82对明确gap影响输入窗口标UNKNOWN。未认证供应商所有缺漏都带断连标记。

## 旧BBO与资源封存

preflight与seal中May文件SHA `e599b118af934cfe45dc3df81330a364b60bf61008d456be674c452a2d3cb246`、241571行；Jun SHA `a50227978d36712ef34413aedea58bb64e6f8df4f6a6106b23ff1b5bef6c5830`、252497行，与旧data-receipt身份相符。core.py:97–126只允许既有项目data路径、禁symlink/路径转出，预检核SHA/schema/UTC日/时序/行数并读至gzip EOF；run.py:18–22正式前再核封存身份与压缩SHA。没有调用旧experiment.py。原件旧QC与新preflight的实际完成声明依相应回执，不由本Reviewer重跑认证。

本轮仅对小型源文/回执重新做文件SHA：core/run/analysis/tests/parameters均匹配preparation-seal；preflight与reuse-amendment SHA也匹配seal，当前计划SHA匹配。amendment的current_sources等于seal.sources；历史快照analysis/tests匹配original_sources，其他三个未变文件的当前SHA本来即匹配preflight记录。未读行情体或重算BBO hash。

Budget(core.py:46–82)累加resource-*.json中的既有compute/network/bytes/GET，执行时用1800s计算、1800s网络、512MiB RSS、256MiB Owner磁盘、64MiB总体下载、288 GET及固定主动deadline保护；网络/等待另计，单线程。preparation-budget含Root180s+10s计算、60s网络、1MiB资料预留并明确为保守预留而非Owner实测；Owner实际新行情GET/字节为0。正式release绑定preparation-seal SHA，run.py核来源/参数/计划/preflight不变，first-started限制一次启动。预算是停止帽，不保证288片可得或两日评分成功；真实资源与失败片须后续审原件。周期RSS/磁盘guard不是绝对无瞬时越界证明。

## 口径限制

这里只检查数据入口、解析/身份、资源及封存链，不独立认可D公式/统计区间/经济条件。原生记录为供应商采集钟；与BBO配对、源钟约束和实际覆盖必须正式数据QC，不从目录或预检盘口通过推定≥80%。五月六月源码页字段同一性仍须逐片实核；七位时钟若不符则按固定方案输入失败，不临时适配精度择优。原生方向信息不能证明个人收到消息/撤单的真实时点或自身成交。

审阅对象：preflight.json、preparation-seal.json、preflight-reuse-amendment.json、parameters.json、preparation-budget.json、resource-reservations.json、run.py/core.py全文及analysis.py数据配对/输入gap相关段；小范围读取冻结提案当前相关段。审阅时preparation-seal SHA为`1ff44d5377b4d15a83d54ab7c5ac0436497b32362e29981e47d4778cfc7f7a28`。本must_fix状态基于该版本，Owner后续修正须Root审新回执，不能沿用本报告替新版本背书。

保存UTC：2026-10-22T00:18:00.459493+00:00；实际model/effort UNKNOWN。

## Runtime整改验收追加

**原MUST_FIX已闭合，来源与数据QC静态结论更新为PASS_WITH_LIMITS。**

新preparation-seal SHA256为`f2a724017607c944f32da7cbf0ddbef0503d65fa9ae5300704fd6550cbe34a99`；本轮独立重算小型文件hash匹配。run.py新SHA为`430b521c3e1e6a9dde249cc2805ee61682701b37a54a2be5c6df61ff16091b91`，实际diff与runtime-binding.diff相同，只新增validate_runtime及正式入口调用：同时比对sys.executable与sys.version，先于正式数据获取执行。

formal_runtime固定`/Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/.venv/bin/python`，版本3.12.14，与原preflight.Python及runtime-binding-check.actual_runtime一致。check记录实际预检解释器接受、错路径/旧3.9拒绝且GET/real-input-open/labels均0；本Reviewer仅读回执，不再执行这些检查。amendment所绑定check哈希、新seal所绑定amendment哈希均匹配；core/analysis/tests/parameters仍匹配新seal，不因runtime整改漂移。

旧seal在before-runtime-binding中保留，其SHA匹配prior_seal_sha256；更正将3.9明确归为旧metadata写入进程而非真实预检环境，不追溯冒充新运行。此前数据/资源/缺口限制完整保留；不代替Root正式release、方法审阅或后续真实输入验收。无网络、行情、源码执行或QC重跑。

追加UTC：2026-10-22T00:18:43.666224+00:00
